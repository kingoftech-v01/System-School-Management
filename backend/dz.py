# Static Folder Name
folder_name = "w3crm"

dz_array = {
    "public": {
        "favicon": f"{folder_name}/images/favicon.png",
        "description": "School Management System",
        "og_title": "School Management System",
        "og_description": "School Management System",
        "og_image": "",
        "title": "School Management System",
    },
    "global": {
        "css": [
            f"{folder_name}/vendor/bootstrap-select/dist/css/bootstrap-select.min.css",
            f"{folder_name}/css/style.css",
        ],
        "js": {
            "top": [
                f"{folder_name}/vendor/global/global.min.js",
                f"{folder_name}/vendor/bootstrap-select/dist/js/bootstrap-select.min.js",
            ],
            "bottom": [
                f"{folder_name}/js/custom.min.js",
                f"{folder_name}/js/deznav-init.js",
            ],
        },
    },
    "pagelevel": {},
}
