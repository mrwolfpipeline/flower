from PySide2.QtWidgets import QApplication, QComboBox, QStyledItemDelegate, QListView, QCheckBox
from PySide2.QtCore import Qt


class CheckableComboBox(QComboBox):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setView(QListView())

        self._delegate = CheckableComboBoxView(self)
        self.setItemDelegate(self._delegate)

    def addItem(self, text):
        super().addItem(text)
        index = self.model().index(self.count() - 1, 0)
        self.model().setData(index, Qt.Unchecked, Qt.CheckStateRole)


class CheckableComboBoxView(QStyledItemDelegate):
    def __init__(self, parent=None):
        super().__init__(parent)

    def createEditor(self, parent, option, index):
        checkbox = QCheckBox(parent)
        checkbox.clicked.connect(lambda: self.toggle_checked_state(checkbox, index))
        return checkbox

    def setEditorData(self, editor, index):
        value = index.data(Qt.CheckStateRole)
        editor.setChecked(value == Qt.Checked)

    def setModelData(self, editor, model, index):
        model.setData(index, Qt.Checked if editor.isChecked() else Qt.Unchecked, Qt.CheckStateRole)

    def toggle_checked_state(self, checkbox, index):
        model = index.model()
        state = Qt.Checked if checkbox.isChecked() else Qt.Unchecked
        model.setData(index, state, Qt.CheckStateRole)


if __name__ == "__main__":
    import sys

    app = QApplication(sys.argv)
    combo = CheckableComboBox()
    combo.addItem("Item 1")
    combo.addItem("Item 2")
    combo.addItem("Item 3")
    combo.addItem("Item 4")
    combo.show()
    sys.exit(app.exec_())
