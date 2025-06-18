collections = {
    "i009501:invekos_feldstuecke_2024_2" : "fieldparcels",
    "i009501:invekos_hofstellen_2024_2": "farmsteads",
    "i009501:invekos_referenzen_2024_2_point": "point_references",
    "i009501:invekos_referenzen_2024_2_polygon": "polygon_references", 
    "i009501:invekos_schlaege_2024_2_point" : "point_plots", 
    "i009501:invekos_schlaege_2024_2_polygon" : "polygon_plots", 
}

attributes = {
    "betr_id": {
        "name": "tech_id",
        "type": "Number",
        "description": "Technical ID of the farm",
        "collections": ["farmsteads"]
    },
    "fs_kennung": {
        "name": "fs_kennung",
        "type": "Number",
        "description": "Connects declared plots to registered land",
        "collections": ["fieldparcels", "point_plots", "polygon_plots"]
    },
    "referenz_kennung": {
        "name": "ref_id",
        "type": "Number",
        "description": "Technical ID for a reference object like landscape features used for agricultural subsidies",
        "collections": ["point_references", "polygon_references"]
    },
    "ref_art": {
        "name": "ref_type",
        "type": "Text",
        "description": "Type of reference feature (e.g., hedge, ditch, stone wall)",
        "collections": ["point_references", "polygon_references"]
    },
    "ref_art_bezeichnung": {
        "name": "ref_type_name",
        "type": "Text",
        "description": "Name of the reference feature type (ref_type)",
        "collections": ["point_references", "polygon_references"]
    },
    "snar_code": {
        "name": "snar_code",
        "type": "Text",
        "description": "Declared land use code",
        "collections": ["point_plots", "polygon_plots"]
    },
    "snar_bezeichnung": {
        "name": "snar_name",
        "type": "Text",
        "description": "Name of the declared land use code (snar_code)",
        "collections": ["point_plots", "polygon_plots"]
    },
    "gml_geom": {
        "name": "gml_geometry",
        "type": "Text",
        "description": "Geometry of the feature",
        "collections": ["fieldparcel", "farmsteads", "point_plots", "polygon_plots", "point_references", "polygon_references"]
    },
    "gml_id": {
        "name": "gml_id",
        "type": "Text",
        "description": "GML ID of the feature",
        "collections": ["fieldparcel", "farmsteads", "point_plots", "polygon_plots", "point_references", "polygon_references"]
    },
    "gml_identifier": {
        "name": "gml_identifier",
        "type": "Text",
        "description": "GML identifier of the feature (link)",
        "collections": ["fieldparcel", "farmsteads", "point_plots", "polygon_plots", "point_references", "polygon_references"]
    },
    "gml_length": {
        "name": "gml_length",
        "type": "Number",
        "description": "The length or perimeter of the geometry in meters",
        "collections": ["fieldparcel", "farmsteads", "point_plots", "polygon_plots", "point_references", "polygon_references"]
    },
    "geo_type": {
        "name": "geo_type",
        "type": "Text",
        "description": "Type of the geometry (e.g., Point, Polygon)",
        "collections": ["point_plots", "polygon_plots", "point_references", "polygon_references"]
    },
    "geo_id": {
        "name": "geo_id",
        "type": "Number",
        "description": "Internal identifier linking geometry to a spatial database or table",
        "collections": ["fieldparcel", "point_plots", "polygon_plots"]
    },
    "geo_part_key": {
        "name": "geo_part_key",
        "type": "Number",
        "description": "A technical key referencing subcomponents of geometry (used in complex geometries or multipolygons)",
        "collections": ["fieldparcel"]
    },
    "geom_date_created": {
        "name": "geom_date_created",
        "type": "DateTime",
        "description": "The date when a geometry was first created in the system. Used for version control and audit trails.",
        "collections": ["fieldparcel", "point_plots", "polygon_plots"]
    },
    "geo_daterf": {
        "name": "geo_daterf",
        "type": "DateTime",
        "description": "The date when the geometry was last modified or referenced. Important for tracking changes.",
        "collections": ["point_references", "polygon_references"]
    },
    "fs_flaeche_ha": {
        "name": "fieldparcel_area",
        "type": "Number",
        "description": "Area of the field parcel in hectares",
        "collections": ["fieldparcels"]
    },
    "sl_flaeche_brutto_ha": {
        "name": "fieldplot_area_gross",
        "type": "Number",
        "description": "Gross area of the declared plot (plot) in hectares. May differ from cadastral if boundaries vary slightly.",
        "collections": ["point_plots", "polygon_plots"]
    },
    "bruttoflaeche_ha": {
        "name": "reference_area_gross",
        "type": "Number",
        "description": "Gross area of a reference feature (e.g., hedge, buffer strip). Important for compliance with EU agricultural policy",
        "collections": ["point_references", "polygon_references"]
    },
    "fart_id": {
        "name": "funding_id",
        "type": "Number",
        "description": "Identifier for the funding type. It links to agricultural programs, e.g., greening, ÖPUL (Austrian agri-environmental program), CAP schemes.",
        "collections": ["fieldparcel", "farmsteads", "point_plots", "polygon_plots", "point_references", "polygon_references"]
    },
    "kz_bio_oepul_jn": {
        "name": "organic_certification",
        "type": "Text",
        "description": "Binary flag indicating yes (`J`) or no (`N`) if the plot is part of a bio/ÖPUL program.",
        "collections": ["point_plots", "polygon_plots"]
    },
    "fnar_code": {
        "name": "field_use_code",
        "type": "Text",
        "description": "Code for the field use type as per national agricultural classification (e.g., arable land, pasture, fallow)",
        "collections": ["fieldparcels"]
    },
    "fnar_bezeichnung": {
        "name": "field_use_name",
        "type": "Text",
        "description": "Text description of the `fnar_code` (e.g., “Dauergrünland” = permanent grassland).",
        "collections": ["fieldparcels"]
    },
    "log_pkey": {
        "name": "log_pkey",
        "type": "Number",
        "description": "Log primary key. Used for versioning and tracking changes in the database.",
        "collections": ["fieldparcels", "point_plots", "polygon_plots"]
    },
    "inspire_id": {
        "name": "inspire_id",
        "type": "Text",
        "description": "Unique identifier for the feature in the INSPIRE (Infrastructure for Spatial Information in Europe) framework. (link)",
        "collections": ["fieldparcels", "farmsteads", "point_plots", "polygon_plots", "point_references", "polygon_references"]
    },
}