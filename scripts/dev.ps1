Write-Host "Running Ruff..."
ruff check . --fix

Write-Host "Running Black..."
black .

Write-Host "Running Tests..."
pytest