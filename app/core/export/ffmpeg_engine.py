import ffmpeg
from pathlib import Path
from core.project import Project, Clip, TextOverlay, Filters
from core.export.engine_interface import IRenderEngine, RenderError
from core.export.export_profile import ExportProfile

class FfmpegRenderEngine(IRenderEngine):
    """Implémentation du moteur de rendu utilisant ffmpeg-python."""

    def render(self, 
               project: Project, 
               output_path: Path, 
               profile: ExportProfile) -> None:
        """
        Construit et exécute la commande FFmpeg 
        basée sur l'objet Project et le Profil.
        """
        try:
            fps = project.fps
            w, h = project.resolution

            # Charger et trimmer chaque clip
            videos, audios = [], []
            for clip_data in project.clips:
                v, a = self._make_trimmed_stream(clip_data, fps)
                videos.append(v); audios.append(a)
            
            if not videos:
                raise RenderError("Le projet est vide, aucun clip à exporter.")

            # Concat
            concat = ffmpeg.concat(*[x for pair in zip(videos, audios) for x in pair],
                                   v=1, a=1).node
            vcat, acat = concat[0], concat[1]

            # Filtres vidéo globaux
            v = self._build_filter_chain(vcat, project.filters, w, h)

            # Overlays de texte
            v = self._apply_text_overlays(v, project.text_overlays)

            # Audio
            a = acat
            if project.audio_normalize:
                a = a.filter('loudnorm', i='-16', tp='-1.5', lra='11')

            # Encodage (utilisation de profil)
            encoding_args = profile.to_ffmpeg_args()
            encoding_args['r'] = fps

            output_path.parent.mkdir(parents=True, exist_ok=True)
            stream = ffmpeg.output(
                v, a, str(output_path),
                **encoding_args
            )
            
            print("Commande FFmpeg :", ffmpeg.compile(stream))
            ffmpeg.run(stream, overwrite_output=True) 

        except ffmpeg.Error as e:
            error_msg = e.stderr.decode() if e.stderr else str(e)
            print("Erreur FFmpeg :", error_msg)
            raise RenderError(f"Échec du rendu FFmpeg : {error_msg}")
        except Exception as e:
            raise RenderError(f"Erreur inattendue lors du rendu : {e}")
    
    def _make_trimmed_stream(self, clip: Clip, fps: int):
        inp = ffmpeg.input(clip.path)
        start, end = clip.trim
        dur = max(0, end - start)
        
        vid_stream = ffmpeg.trim(inp, start=start, duration=dur).setpts('PTS-STARTPTS')
        aud_stream = (ffmpeg.input(clip.path)
                           .filter_('atrim', start=start, duration=dur)
                           .filter_('asetpts', 'PTS-STARTPTS'))
        
        vid_stream = vid_stream.filter('fps', fps=fps)
        return vid_stream, aud_stream

    def _build_filter_chain(self, vid, filters: Filters, w: int, h: int):
        vid = vid.filter("scale", w, h)
        vid = vid.filter('eq',
                         brightness=filters.brightness,
                         contrast=filters.contrast,
                         saturation=filters.saturation)
        if filters.vignette:
            vid = vid.filter('vignette', angle='PI/4', x0='w/2', y0='h/2')
        return vid

    def _apply_text_overlays(self, vid, overlays: list[TextOverlay]):
        for ov in overlays:
            fontfile = ov.fontfile.replace("\\", "/") if ov.fontfile else ""
            
            draw = {
                'text': ov.text,
                'x': ov.x, 'y': ov.y,
                'fontsize': ov.fontsize, 'fontcolor': ov.fontcolor,
                'enable': f"between(t,{ov.start},{ov.end})",
            }
            if fontfile:
                draw['fontfile'] = fontfile
                
            if ov.box:
                draw.update({
                    'box': 1, 'boxcolor': ov.boxcolor, 
                    'boxborderw': ov.boxborderw
                })
            vid = vid.filter('drawtext', **draw)
        return vid