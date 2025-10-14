from pathlib import Path
from PySide6.QtCore import Qt, QUrl
from PySide6.QtWidgets import QInputDialog, QWidget, QVBoxLayout, QFileDialog, QMessageBox, QSplitter

from ui.editor.video_canvas import VideoCanvas
from ui.editor.player_controls import PlayerControls
from ui.editor.timeline import TimelineScroll
from ui.editor.inspector import Inspector
from core.media_controller import MediaController
from core.store import Store
from engine.exporter import Exporter
from ui.editor.assets_panel import AssetsPanel

class EditorWindow(QWidget):
    def __init__(self, store: Store, parent=None): 
        super().__init__()
        self.resize(1280, 720)

        # back
        self.media = MediaController(self)
        self.store = store
        self.exporter = Exporter()

        # centre vidéo (canvas)
        self.canvas = VideoCanvas()
        #self.canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self.controls = PlayerControls()
        self.controls.set_media(self.media)

        # timeline
        self.timeline_scroll = TimelineScroll(self)
        self.timeline = self.timeline_scroll.timeline
        self.timeline.imageDropped.connect(self.on_timeline_drop_image)

        self.inspector = Inspector(self)
        #self.inspector.setMinimumWidth(260)
        #self.inspector.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)

        self.assets = AssetsPanel(self)

        #self.canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        #self.assets.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        #self.inspector.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        # --- Layout racine (UN SEUL) ---
        #main_layout = QVBoxLayout(self)
        #main_layout.setContentsMargins(6, 6, 6, 6)
       # #main_layout.setSpacing(6)

        #top_layout = QHBoxLayout()
        #top_layout.setContentsMargins(0, 0, 0, 0)
        #top_layout.setSpacing(6)

        # Colonne gauche : Import + Assets
        #left_col = QVBoxLayout()
        #left_col.setContentsMargins(0, 0, 0, 0)
        #left_col.setSpacing(6)
        #left_col.addWidget(self.assets, stretch=1)

        # Colonne centre : Vidéo + Controls
        #center_col = QVBoxLayout()
        #center_col.setContentsMargins(0, 0, 0, 0)
        #center_col.setSpacing(6)
        #center_col.addWidget(self.canvas, stretch=3)
        #center_col.addLayout(self.controls)

        # Colonne droite : Inspector
        #right_col = QVBoxLayout()
        #right_col.setContentsMargins(0, 0, 0, 0)
        #right_col.setSpacing(6)
        #right_col.addWidget(self.inspector, stretch=1)

        #top_layout.addLayout(left_col, 1)
        #top_layout.addLayout(center_col, 3)
        #top_layout.addLayout(right_col, 1)


        #main_layout.addLayout(top_layout, 5)
        #main_layout.addWidget(self.timeline_scroll, 1)

        # Colonne Gauche (Assets) : doit pouvoir se rétrécir mais rester lisible.
        self.assets.setMinimumWidth(150) # AJOUTÉ : Taille minimale pour Assets

        # Colonne Centre (Canvas + Controls) : doit avoir une taille minimale pour la vidéo.
        self.canvas.setMinimumSize(300, 200) # AJOUTÉ : Taille minimale pour la zone vidéo

        # Colonne Droite (Inspector) : a déjà 100 de minimum dans votre code ci-dessous.

        # Timeline : Assure une hauteur minimale pour la timeline.
        # Note : Votre classe TimelineScroll/TimelineWidget doit gérer son MinimumHeight correctement.
        if hasattr(self.timeline, 'setMinimumHeight'):
             self.timeline.setMinimumHeight(100) 

        self.center_container = QWidget()
        center_col_layout = QVBoxLayout(self.center_container)
        center_col_layout.setContentsMargins(0, 0, 0, 0)
        center_col_layout.setSpacing(6)

        center_col_layout.addWidget(self.canvas, stretch=3) 
        center_col_layout.addWidget(self.controls) 

        top_splitter = QSplitter(Qt.Orientation.Horizontal)


        top_splitter.addWidget(self.assets)          # Colonne gauche
        top_splitter.addWidget(self.center_container) # Colonne centre (Canvas + Controls)
        top_splitter.addWidget(self.inspector)

        top_splitter.setSizes([200, 600, 200])

        self.inspector.setMinimumWidth(100)

        main_splitter = QSplitter(Qt.Orientation.Vertical)
        
        main_splitter.addWidget(top_splitter)          # La zone supérieure complète
        main_splitter.addWidget(self.timeline_scroll)  # La Timeline

        main_splitter.setSizes([500, 100])
        
        # --- 4. Layout racine (UN SEUL) ---
        # Le layout principal contient désormais uniquement le splitter principal
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(6, 6, 6, 6)
        main_layout.setSpacing(6)
        main_layout.addWidget(main_splitter)

        self.setLayout(main_layout)


        # Wiring vidéo et timeline (inchangé)
        self.media.frameImageAvailable.connect(self.canvas.set_frame)
        self.media.positionChanged.connect(self.canvas.set_playhead_ms)
        self.canvas.set_project(self.store.project())
        self.timeline.seekRequested.connect(self.media.seek_ms)
        self.media.durationChanged.connect(self.timeline.set_duration)
        self.media.positionChanged.connect(self.timeline.set_position)
        self.media.errorOccurred.connect(self._on_media_error)
        self.media.durationChanged.connect(self.controls.set_duration)
        self.media.positionChanged.connect(self.controls.set_position)

        # Actions
        self.controls.openRequested.connect(self._open_file)
        self.controls.exportRequested.connect(self._export)
        self.controls.zoomChanged.connect(self.timeline.set_zoom)
        self.controls.seekRelativeRequested.connect(self.media.seek_relative_ms)


        # Inspector ↔ Store
        self.inspector.addTitleRequested.connect(lambda: (self.store.add_text_overlay(), self._refresh_overlay()))
        self.inspector.removeTitleRequested.connect(lambda: (self.store.remove_last_text_overlay(), self._refresh_overlay()))
        self.inspector.titleTextChanged.connect(lambda txt: (self.store.update_last_overlay_text(txt), self._refresh_overlay()))
        self.inspector.filtersChanged.connect(self._on_filters_changed)
        self.inspector.setTitleStartRequested.connect(self._apply_title_start_from_playhead)
        self.inspector.setTitleEndRequested.connect(self._apply_title_end_from_playhead)
        self.store.overlayChanged.connect(self._refresh_overlay)
        self._refresh_overlay()

    # ----- actions -----
    def _open_file(self):
        start_dir = str(Path.cwd() / "assets")
        f, _ = QFileDialog.getOpenFileName(
            self, "Ouvrir une vidéo", start_dir,
            "Vidéos (*.mp4 *.mov *.mkv *.avi);;Tous les fichiers (*.*)"
        )
        if not f: return
        self.media.load(QUrl.fromLocalFile(f))
        self.media.play()
        # provisoire: clip unique avec une durée par défaut (ajustable après)
        self.store.set_clip(f, duration_s=5.0)

    def _export(self):
        proj = self.store.project()
        src = proj.clips[0].path if proj.clips else (str(Path("assets") / "Fluid_Sim_Hue_Test.mp4"))
        try:
            out_path = self.exporter.export_from_project(proj, fallback_src=src)
            QMessageBox.information(self, "Export", f"Fichier exporté : {out_path}")
        except Exception as e:
            QMessageBox.critical(self, "Export échoué", str(e))

    def _on_media_error(self, text: str):
        if text:
            QMessageBox.warning(self, "Avertissement média", text)

    def _on_filters_changed(self, b, c, s, v):
        self.store.set_filters(brightness=b, contrast=c, saturation=s, vignette=v)

    def _apply_title_start_from_playhead(self):
        ms = self.media.position_ms()
        self.store.set_last_overlay_start(ms / 1000.0)
        self._refresh_overlay()

    def _apply_title_end_from_playhead(self):
        ms = self.media.position_ms()
        self.store.set_last_overlay_end(ms / 1000.0)
        self._refresh_overlay()

    def _refresh_overlay(self):
        self.canvas.set_project(self.store.project())
        self.timeline.set_overlays([
            {"start": ov.start, "end": ov.end, "label": (ov.text or "Titre")}
            for ov in self.store.project().text_overlays
        ])
        self.timeline.update()

    def _add_to_timeline(self, file_path):
        """Ajoute le média importé directement à la timeline et au store."""
        self.store.set_clip(file_path)
        self.media.load(QUrl.fromLocalFile(file_path))

    def _prompt_for_project(self):
        """Affiche une boîte de dialogue pour choisir entre nouveau projet ou chargement."""
        msgBox = QMessageBox(self)
        msgBox.setWindowTitle("Démarrer votre session")
        msgBox.setText("Que voulez-vous faire ?")
        msgBox.setInformativeText("Un nouveau projet vierge est chargé par défaut.")
        
        new_project_btn = msgBox.addButton("Nouveau Projet", QMessageBox.AcceptRole)
        load_project_btn = msgBox.addButton("Charger un Projet", QMessageBox.ActionRole)
        msgBox.setDefaultButton(new_project_btn)

        msgBox.exec()
        
        clicked_button = msgBox.clickedButton()

        if clicked_button == load_project_btn:
            self._open_load_dialog()
            
        elif clicked_button == new_project_btn:
            new_name, ok = QInputDialog.getText(
                self, 
                "Nommer votre projet", 
                "Entrez le nom du nouveau projet:",
                text=self.store.project().name
            )
            
            if ok and new_name and new_name != self.store.project().name:
                self.store.set_project_name(new_name)
                print(f"Action: Nouveau projet nommé : {new_name}")
            elif ok:
                print("Action: Nouveau projet conservant le nom par défaut.")
            else:
                print("Création du nouveau projet annulée (nom par défaut conservé).")
            
    def _open_load_dialog(self):
        """Ouvre la boîte de dialogue standard pour sélectionner un fichier .lmprj."""
        from core.save_system.serializers import LMPRJChunkedSerializer
        import os
        
        save_dir = LMPRJChunkedSerializer.get_save_dir()
        
        selected_file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Charger un projet Luminare (.lmprj)",
            save_dir,
            "Fichiers Projet Luminare (*.lmprj)"
        )

        if selected_file_path:
            filename_to_load = os.path.basename(selected_file_path)
            self.store.load_project(filename_to_load)
            proj = self.store.project()
            if proj.clips:
                 self.media.load(QUrl.fromLocalFile(proj.clips[0].path))
                 self.media.seek_ms(0)
                 self._refresh_overlay()
        else:
            print("Chargement annulé, conservation du projet actuel.")

    def setup_project_on_entry(self):
        """
        Gère le dialogue de choix Nouveau/Charger. 
        À appeler juste avant de rendre l'éditeur visible.
        """
        self._prompt_for_project() 
        self._refresh_overlay()
        self.setWindowTitle(f"Luminare — {self.store.project().name}")