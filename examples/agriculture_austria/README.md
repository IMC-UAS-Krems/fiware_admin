# Agriculture Usecase in Austria

A use case about the different landuse in agriculture in Austria. The dataset is from GeoServer, an austrian governmental website.
The attributes taken are
-   funding: funding number refers to which organisation funds the parcel of land
-   field_parcel_id: a specific identifier for the parcel
-   dateObserved: when the parcel was logged in the system
-   location: in geo:json format to log the entity on the map
-   area: the area of the parcel (note: I can't seem to see the area on the dashboard but it is logged successfully in the database)
-   length: the length of the parcel
-   organisation_a, organisation_b, organisation_c, organisation_d, organisation_e
-   farmland, wineyard, grassland
-   gml_id: identifier according to gml standards
-   measurand: list of the numerical attributes

## Pie
In order to visualize the funding count in the pie, I hot encoded the funding type attribute into 5 binary representations, otherwise the pie wouldn't show the variation of the different funding. I did the same for landuse.

## Different choices 
-   In order to visualize all points on the map, select choice 3
-   In order to visualize both pies, select choice 2
-   In order to visualize the funding pie and 3 points on the map, select choice 1

See bellow to see how to use this 

## Usage
1. Make the json file, from the fiware_admin repository, run
```bash
python examples/agriculture/process_data.py {choice_id}
```

2. Add these lines in fiware_admin.Dockerfile
```bash
  CMD ["bash", "-c", "\
  for file in examples/agriculture_austria/data/fiware_data.json; do \
    echo \"Uploading: $file\"; \
    python fiware_admin.py -c config.json -u \"$file\" --auto-batch || exit 1; \
  done" ]
```

3. Re-run fiware-admin, mongo and orion dockers

4. copy paste the material of template.sdd into the editor