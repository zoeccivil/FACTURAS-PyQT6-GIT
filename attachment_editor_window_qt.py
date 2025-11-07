# attachment_editor_window_qt.py

import os
import traceback
from pathlib import Path
from PIL import Image, ImageEnhance

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QMessageBox,
    QGraphicsView, QGraphicsScene, QFrame, QGraphicsPixmapItem, QGraphicsRectItem,
)
from PyQt6.QtGui import QPixmap, QImage, QPen, QColor, QBrush, QPainter
from PyQt6.QtCore import Qt, QRectF, QPointF, QSizeF, pyqtSignal # <-- 1. IMPORTAR pyqtSignal

# (La clase CropRectItem no necesita cambios, se deja igual)
class CropRectItem(QGraphicsRectItem):
    HANDLE_SIZE = 12

    def __init__(self, rect, parent=None):
        super().__init__(rect, parent)
        try:
            self.setFlag(QGraphicsRectItem.GraphicsItemFlag.ItemIsMovable, True)
            self.setFlag(QGraphicsRectItem.GraphicsItemFlag.ItemIsSelectable, True)
            self.setFlag(QGraphicsRectItem.GraphicsItemFlag.ItemSendsGeometryChanges, True)
            self.setFlag(QGraphicsRectItem.GraphicsItemFlag.ItemIsFocusable, True)
            self.setAcceptHoverEvents(True)
        except Exception:
            pass
        self.handles = {}
        self.handle_selected = None
        self.mouse_press_pos = None
        self.mouse_press_rect = None
        self.setPen(QPen(QColor(255, 0, 0), 2, Qt.PenStyle.DashLine))
        self.setBrush(QBrush(QColor(255, 0, 0, 40)))

    def boundingRect(self):
        o = self.HANDLE_SIZE / 2
        return self.rect().adjusted(-o, -o, o, o)

    def hoverMoveEvent(self, event):
        handle = self.getHandleAt(event.pos())
        cursor = Qt.CursorShape.ArrowCursor
        if handle == 'tl' or handle == 'br':
            cursor = Qt.CursorShape.SizeFDiagCursor
        elif handle == 'tr' or handle == 'bl':
            cursor = Qt.CursorShape.SizeBDiagCursor
        elif handle in ('l', 'r'):
            cursor = Qt.CursorShape.SizeHorCursor
        elif handle in ('t', 'b'):
            cursor = Qt.CursorShape.SizeVerCursor
        elif handle == 'move':
            cursor = Qt.CursorShape.SizeAllCursor
        self.setCursor(cursor)
        super().hoverMoveEvent(event)

    def mousePressEvent(self, event):
        self.handle_selected = self.getHandleAt(event.pos())
        self.mouse_press_pos = event.pos()
        self.mouse_press_rect = self.rect()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self.handle_selected and self.handle_selected != 'move':
            self.interactiveResize(self.handle_selected, event.pos())
        elif self.handle_selected == 'move':
            diff = event.pos() - self.mouse_press_pos
            new_rect = QRectF(self.mouse_press_rect)
            new_rect.moveTopLeft(new_rect.topLeft() + diff)
            self.setRect(new_rect)
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        self.handle_selected = None
        super().mouseReleaseEvent(event)

    def getHandleAt(self, point):
        rect = self.rect()
        o = self.HANDLE_SIZE
        handles = {
            'tl': QRectF(rect.topLeft() - QPointF(o / 2, o / 2), QSizeF(o, o)),
            'tr': QRectF(rect.topRight() - QPointF(o / 2, o / 2), QSizeF(o, o)),
            'bl': QRectF(rect.bottomLeft() - QPointF(o / 2, o / 2), QSizeF(o, o)),
            'br': QRectF(rect.bottomRight() - QPointF(o / 2, o / 2), QSizeF(o, o)),
            't': QRectF(rect.center().x() - o / 2, rect.top() - o / 2, o, o),
            'b': QRectF(rect.center().x() - o / 2, rect.bottom() - o / 2, o, o),
            'l': QRectF(rect.left() - o / 2, rect.center().y() - o / 2, o, o),
            'r': QRectF(rect.right() - o / 2, rect.center().y() - o / 2, o, o),
        }
        for key, value in handles.items():
            if value.contains(point):
                return key
        if rect.contains(point):
            return 'move'
        return None

    def interactiveResize(self, handle, mouse_pos):
        rect = QRectF(self.mouse_press_rect)
        diff = mouse_pos - self.mouse_press_pos
        if handle == 'tl':
            rect.setTopLeft(rect.topLeft() + diff)
        elif handle == 'tr':
            rect.setTopRight(rect.topRight() + diff)
        elif handle == 'bl':
            rect.setBottomLeft(rect.bottomLeft() + diff)
        elif handle == 'br':
            rect.setBottomRight(rect.bottomRight() + diff)
        elif handle == 't':
            rect.setTop(rect.top() + diff.y())
        elif handle == 'b':
            rect.setBottom(rect.bottom() + diff.y())
        elif handle == 'l':
            rect.setLeft(rect.left() + diff.x())
        elif handle == 'r':
            rect.setRight(rect.right() + diff.x())
        self.setRect(rect.normalized())

    def paint(self, painter, option, widget=None):
        super().paint(painter, option, widget)
        o = self.HANDLE_SIZE
        rect = self.rect()
        points = [
            rect.topLeft(), rect.topRight(), rect.bottomLeft(), rect.bottomRight(),
            QPointF(rect.center().x(), rect.top()),
            QPointF(rect.center().x(), rect.bottom()),
            QPointF(rect.left(), rect.center().y()),
            QPointF(rect.right(), rect.center().y()),
        ]
        for pt in points:
            painter.setBrush(QColor(255, 255, 255))
            painter.setPen(QPen(QColor(255, 0, 0), 1))
            painter.drawRect(QRectF(pt.x() - o / 2, pt.y() - o / 2, o, o))


class AttachmentEditorWindowQt(QDialog):
    # <-- 2. AÑADIR SEÑAL. Emitirá la ruta de la imagen guardada.
    saved = pyqtSignal(str)

    def __init__(self, parent, image_path, width=1200, height=800):
        super().__init__(parent)
        self.setWindowTitle("Editor de Imagen")
        self.resize(1000, 800)
        # <-- 3. ESTABLECER COMO NO MODAL
        self.setWindowModality(Qt.WindowModality.NonModal)
        self.image_path = image_path
        self.width_destino = width
        self.height_destino = height

        try:
            self.original_image = Image.open(self.image_path).convert("RGB")
            self.current_image = self.original_image.copy()
        except Exception as e:
            tb = traceback.format_exc()
            QMessageBox.critical(self, "Error al abrir imagen", f"No se pudo abrir la imagen:\n{e}\n\n{tb}")
            self.reject()
            return

        try:
            self.scene = QGraphicsScene(self)
            self.view = QGraphicsView(self.scene)
            try:
                self.view.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
            except Exception:
                pass
            self.view.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
            self.view.setResizeAnchor(QGraphicsView.ViewportAnchor.AnchorViewCenter)
            self.view.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
            self.view.setFrameShape(QFrame.Shape.NoFrame)
            self.crop_item = None
            self._build_ui()
            self.update_image_display()
        except Exception as e:
            tb = traceback.format_exc()
            QMessageBox.critical(self, "Error UI", f"Error construyendo el editor:\n{e}\n\n{tb}")
            self.reject()
            return

    def _build_ui(self):
        main_layout = QVBoxLayout(self)
        toolbar_layout = QHBoxLayout()

        btn_zoom_in = QPushButton("Zoom +")
        btn_zoom_in.clicked.connect(self.zoom_in)
        btn_zoom_out = QPushButton("Zoom -")
        btn_zoom_out.clicked.connect(self.zoom_out)
        btn_fit_view = QPushButton("Ajustar a la Vista")
        btn_fit_view.clicked.connect(self.fit_to_view)
        btn_rotate = QPushButton("Rotar 90°")
        btn_rotate.clicked.connect(self.rotate_image)
        btn_contrast = QPushButton("Contraste +")
        btn_contrast.clicked.connect(self.enhance_contrast)
        self.btn_crop = QPushButton("Recortar")
        self.btn_crop.clicked.connect(self.toggle_crop_mode)
        btn_save = QPushButton("Guardar")
        btn_save.clicked.connect(self.save_changes)
        # <-- 5. CAMBIAR BOTÓN A "CERRAR"
        btn_close = QPushButton("Cerrar")
        btn_close.clicked.connect(self.close) # Usar close() para ventanas no modales

        toolbar_layout.addWidget(btn_zoom_in)
        toolbar_layout.addWidget(btn_zoom_out)
        toolbar_layout.addWidget(btn_fit_view)
        toolbar_layout.addWidget(btn_rotate)
        toolbar_layout.addWidget(btn_contrast)
        toolbar_layout.addWidget(self.btn_crop)
        toolbar_layout.addStretch()
        toolbar_layout.addWidget(btn_save)
        toolbar_layout.addWidget(btn_close)

        main_layout.addLayout(toolbar_layout)
        main_layout.addWidget(self.view)

    def save_changes(self):
        try:
            # --- VALIDACIÓN CRÍTICA (se mantiene igual) ---
            if not isinstance(self.width_destino, (int, float)) or self.width_destino <= 0:
                QMessageBox.critical(self, "Error de Dimensiones", f"El ancho de destino es inválido: {self.width_destino}")
                return
            if not isinstance(self.height_destino, (int, float)) or self.height_destino <= 0:
                QMessageBox.critical(self, "Error de Dimensiones", f"La altura de destino es inválida: {self.height_destino}")
                return
            # --- FIN DE LA VALIDACIÓN ---

            # Hacemos una copia para no modificar la imagen actual en el editor
            img_to_save = self.current_image.copy()
            
            # --- LÍNEA CLAVE CORREGIDA ---
            # Usamos thumbnail para redimensionar proporcionalmente
            img_to_save.thumbnail(
                (int(self.width_destino), int(self.height_destino)), 
                Image.Resampling.LANCZOS
            )
            
            # Asegurarse de que el directorio existe (se mantiene igual)
            dirp = os.path.dirname(self.image_path)
            if dirp and not os.path.exists(dirp):
                os.makedirs(dirp, exist_ok=True)
                
            img_to_save.save(self.image_path, quality=95, optimize=True)
            QMessageBox.information(self, "Guardado", "Los cambios han sido guardados.")
            
            self.saved.emit(self.image_path)
            self.close()
            
        except Exception as e:
            tb = traceback.format_exc()
            QMessageBox.critical(self, "Error al Guardar", f"No se pudo guardar la imagen:\n{e}\n\n{tb}")
    # (El resto del archivo AttachmentEditorWindowQt no necesita más cambios)
    def pil_to_qpixmap(self, pil_image):
        """
        Convierte una imagen de Pillow a QPixmap de forma robusta.
        """
        try:
            # Asegurarse de que la imagen esté en un formato que QImage entiende bien
            if pil_image.mode == "RGBA":
                format = QImage.Format.Format_RGBA8888
            elif pil_image.mode == "RGB":
                format = QImage.Format.Format_RGB888
            else:
                # Convertir otros modos a RGB
                pil_image = pil_image.convert("RGB")
                format = QImage.Format.Format_RGB888

            # Crear QImage desde los bytes, especificando el stride (bytes por línea)
            qimage = QImage(
                pil_image.tobytes(),
                pil_image.width,
                pil_image.height,
                pil_image.width * len(pil_image.getbands()), # bytes por línea
                format
            )
            return QPixmap.fromImage(qimage)
        except Exception as e:
            print(f"[attachment_editor] ERROR convirtiendo PIL a QPixmap: {e}")
            return QPixmap() # Devuelve un Pixmap vacío en caso de error

    def update_image_display(self):
        try:
            self.scene.clear()
            pixmap = self.pil_to_qpixmap(self.current_image)
            if not pixmap.isNull():
                self.pixmap_item = QGraphicsPixmapItem(pixmap)
                self.scene.addItem(self.pixmap_item)
                self.scene.setSceneRect(0, 0, pixmap.width(), pixmap.height())
                self.fit_to_view()
            if self.crop_item:
                # re-add crop item above pixmap
                self.scene.addItem(self.crop_item)
        except Exception as e:
            tb = traceback.format_exc()
            QMessageBox.critical(self, "Error mostrar imagen", f"No se pudo mostrar la imagen:\n{e}\n\n{tb}")

    def zoom_in(self):
        try:
            self.view.scale(1.2, 1.2)
        except Exception:
            pass

    def zoom_out(self):
        try:
            self.view.scale(1 / 1.2, 1 / 1.2)
        except Exception:
            pass

    def fit_to_view(self):
        try:
            rect = self.scene.sceneRect()
            if rect.isEmpty():
                return
            self.view.fitInView(rect, Qt.AspectRatioMode.KeepAspectRatio)
        except Exception:
            pass

    def rotate_image(self):
        try:
            self.current_image = self.current_image.rotate(90, expand=True)
            self.update_image_display()
        except Exception as e:
            QMessageBox.warning(self, "Error al rotar", str(e))

    def enhance_contrast(self):
        try:
            enhancer = ImageEnhance.Contrast(self.current_image)
            self.current_image = enhancer.enhance(1.25)
            self.update_image_display()
        except Exception as e:
            QMessageBox.warning(self, "Error de contraste", str(e))
    def toggle_crop_mode(self):
        try:
            if self.crop_item:
                self.apply_crop()
                self.btn_crop.setText("Recortar")
            else:
                if not hasattr(self, "pixmap_item") or not self.pixmap_item:
                    return
                rect = self.pixmap_item.boundingRect()
                w = rect.width() * 0.6
                h = rect.height() * 0.6
                x = rect.x() + (rect.width() - w) / 2
                y = rect.y() + (rect.height() - h) / 2
                crop_rect = QRectF(x, y, w, h)
                self.crop_item = CropRectItem(crop_rect)
                self.scene.addItem(self.crop_item)
                self.btn_crop.setText("Aplicar Recorte")
        except Exception as e:
            tb = traceback.format_exc()
            QMessageBox.critical(self, "Error crop", f"No se pudo activar el modo recorte:\n{e}\n\n{tb}")

    def apply_crop(self):
        try:
            if not self.crop_item:
                QMessageBox.warning(self, "Sin selección", "Dibuja o ajusta el recuadro de recorte primero.")
                return
            crop_rect = self.crop_item.rect()
            tl_scene = self.crop_item.mapToScene(crop_rect.topLeft())
            br_scene = self.crop_item.mapToScene(crop_rect.bottomRight())
            pixmap_rect = self.pixmap_item.sceneBoundingRect()
            if pixmap_rect.width() == 0 or pixmap_rect.height() == 0:
                QMessageBox.warning(self, "Error", "No se puede recortar: dimensiones inválidas.")
                return
            w_ratio = self.current_image.width / pixmap_rect.width()
            h_ratio = self.current_image.height / pixmap_rect.height()
            x1 = int((tl_scene.x() - pixmap_rect.left()) * w_ratio)
            y1 = int((tl_scene.y() - pixmap_rect.top()) * h_ratio)
            x2 = int((br_scene.x() - pixmap_rect.left()) * w_ratio)
            y2 = int((br_scene.y() - pixmap_rect.top()) * h_ratio)
            x1, y1 = max(0, x1), max(0, y1)
            x2, y2 = min(self.current_image.width, x2), min(self.current_image.height, y2)
            if x2 - x1 < 10 or y2 - y1 < 10:
                QMessageBox.warning(self, "Recorte inválido", "El área seleccionada es demasiado pequeña.")
                return
            self.current_image = self.current_image.crop((x1, y1, x2, y2))
            try:
                self.scene.removeItem(self.crop_item)
            except Exception:
                pass
            self.crop_item = None
            self.update_image_display()
            self.btn_crop.setText("Recortar")
        except Exception as e:
            tb = traceback.format_exc()
            QMessageBox.critical(self, "Error aplicar recorte", f"No se pudo aplicar el recorte:\n{e}\n\n{tb}")

    def wheelEvent(self, event):
        try:
            if event.angleDelta().y() > 0:
                self.zoom_in()
            else:
                self.zoom_out()
        except Exception:
            pass

    def get_final_image(self):
        try:
            return self.current_image.resize((self.width_destino, self.height_destino), Image.Resampling.LANCZOS)
        except Exception:
            return self.current_image