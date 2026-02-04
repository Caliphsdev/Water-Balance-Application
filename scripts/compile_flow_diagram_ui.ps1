#!/usr/bin/env pwsh
# Compile Flow Diagram Dialog UI Files

Write-Host "Compiling Flow Diagram Dialog UI Files..." -ForegroundColor Cyan
Write-Host ""

cd d:\Projects\dashboard_waterbalance

# Compile Add/Edit Node Dialog
Write-Host "Compiling: Add/Edit Node Dialog..." -ForegroundColor Yellow
pyside6-uic "src/ui/designer/dialogs/add_edit_node_dialog.ui" -o "src/ui/dialogs/generated_ui_add_edit_node_dialog.py"
(Get-Content "src/ui/dialogs/generated_ui_add_edit_node_dialog.py") -replace 'import resources_rc', 'import ui.resources.resources_rc' | Set-Content "src/ui/dialogs/generated_ui_add_edit_node_dialog.py"
Write-Host "  OK" -ForegroundColor Green

# Compile Edit Flow Dialog
Write-Host "Compiling: Edit Flow Dialog..." -ForegroundColor Yellow
pyside6-uic "src/ui/designer/dialogs/edit_flow_dialog.ui" -o "src/ui/dialogs/generated_ui_edit_flow_dialog.py"
(Get-Content "src/ui/dialogs/generated_ui_edit_flow_dialog.py") -replace 'import resources_rc', 'import ui.resources.resources_rc' | Set-Content "src/ui/dialogs/generated_ui_edit_flow_dialog.py"
Write-Host "  OK" -ForegroundColor Green

# Compile Flow Type Selection Dialog
Write-Host "Compiling: Flow Type Selection Dialog..." -ForegroundColor Yellow
pyside6-uic "src/ui/designer/dialogs/flow_type_selection_dialog.ui" -o "src/ui/dialogs/generated_ui_flow_type_selection_dialog.py"
(Get-Content "src/ui/dialogs/generated_ui_flow_type_selection_dialog.py") -replace 'import resources_rc', 'import ui.resources.resources_rc' | Set-Content "src/ui/dialogs/generated_ui_flow_type_selection_dialog.py"
Write-Host "  OK" -ForegroundColor Green

# Compile Balance Check Dialog
Write-Host "Compiling: Balance Check Dialog..." -ForegroundColor Yellow
pyside6-uic "src/ui/designer/dialogs/balance_check_dialog.ui" -o "src/ui/dialogs/generated_ui_balance_check_dialog.py"
(Get-Content "src/ui/dialogs/generated_ui_balance_check_dialog.py") -replace 'import resources_rc', 'import ui.resources.resources_rc' | Set-Content "src/ui/dialogs/generated_ui_balance_check_dialog.py"
Write-Host "  OK" -ForegroundColor Green

# Compile Excel Setup Dialog
Write-Host "Compiling: Excel Setup Dialog..." -ForegroundColor Yellow
pyside6-uic "src/ui/designer/dialogs/excel_setup_dialog.ui" -o "src/ui/dialogs/generated_ui_excel_setup_dialog.py"
(Get-Content "src/ui/dialogs/generated_ui_excel_setup_dialog.py") -replace 'import resources_rc', 'import ui.resources.resources_rc' | Set-Content "src/ui/dialogs/generated_ui_excel_setup_dialog.py"
Write-Host "  OK" -ForegroundColor Green

# Compile Flow Diagram Main Dashboard
Write-Host "Compiling: Flow Diagram Dashboard..." -ForegroundColor Yellow
pyside6-uic "src/ui/designer/dashboards/flow_diagram.ui" -o "src/ui/dashboards/generated_ui_flow_diagram.py"
(Get-Content "src/ui/dashboards/generated_ui_flow_diagram.py") -replace 'import resources_rc', 'import ui.resources.resources_rc' | Set-Content "src/ui/dashboards/generated_ui_flow_diagram.py"
Write-Host "  OK" -ForegroundColor Green

Write-Host ""
Write-Host "All Flow Diagram UI files compiled successfully!" -ForegroundColor Green
