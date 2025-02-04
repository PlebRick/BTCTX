import subprocess

# Core dependencies needed for the backend project
core_packages = {
    "fastapi", "uvicorn", "sqlalchemy", "pydantic", "typer", "python-dotenv", "bcrypt", "setuptools", "wheel"
}

# Get the list of all installed packages
result = subprocess.run(["pip", "list"], capture_output=True, text=True)
lines = result.stdout.splitlines()

# Extract package names from pip list output
installed_packages = [line.split()[0] for line in lines[2:]]

# Identify packages that are not part of the core dependencies
packages_to_uninstall = [pkg for pkg in installed_packages if pkg not in core_packages]

if packages_to_uninstall:
    print("The following packages will be uninstalled:")
    print("\n".join(packages_to_uninstall))

    # Confirm with the user before proceeding
    confirmation = input("Do you want to proceed with uninstalling these packages? (yes/no): ").strip().lower()
    if confirmation == "yes":
        # Uninstall all non-core packages
        subprocess.run(["pip", "uninstall", "-y"] + packages_to_uninstall)
        print("Unnecessary packages have been uninstalled.")
    else:
        print("Operation canceled.")
else:
    print("No unnecessary packages found.")