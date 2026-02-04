# Compilation cheat sheet - run from project root

# === Single File Compilation ===

# Main window
pyside6-uic src/ui/designer/main_window.ui -o src/ui/generated_ui_main_window.py

# Single dashboard
pyside6-uic src/ui/designer/dashboards/calculations.ui -o src/ui/dashboards/generated_ui_calculations.py

# Single dialog
pyside6-uic src/ui/designer/dialogs/data_import.ui -o src/ui/dialogs/generated_ui_data_import.py

# Resources (icons/images)
pyside6-rcc src/ui/resources/resources.qrc -o src/ui/resources/resources_rc.py


# === Batch Compilation ===

# All dashboards at once
Get-ChildItem src/ui/designer/dashboards/*.ui | ForEach-Object {
    $name = $_.BaseName
    pyside6-uic $_.FullName -o "src/ui/dashboards/generated_ui_$name.py"
}

# All dialogs at once
Get-ChildItem src/ui/designer/dialogs/*.ui | ForEach-Object {
    $name = $_.BaseName
    pyside6-uic $_.FullName -o "src/ui/dialogs/generated_ui_$name.py"
}

# Everything (main + dashboards + dialogs + resources)
pyside6-uic src/ui/designer/main_window.ui -o src/ui/generated_ui_main_window.py
Get-ChildItem src/ui/designer/dashboards/*.ui | ForEach-Object {
    $name = $_.BaseName; pyside6-uic $_.FullName -o "src/ui/dashboards/generated_ui_$name.py"
}
Get-ChildItem src/ui/designer/dialogs/*.ui | ForEach-Object {
    $name = $_.BaseName; pyside6-uic $_.FullName -o "src/ui/dialogs/generated_ui_$name.py"
}
pyside6-rcc src/ui/resources/resources.qrc -o src/ui/resources/resources_rc.py
