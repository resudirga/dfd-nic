ATTACH DATABASE 'database/NICA.db' AS 'NICA';

BEGIN;

CREATE TABLE NICA.Health_Facilities
(   id     INTEGER     PRIMARY KEY,
    google_pid  INTEGER,        
    name        TEXT,
    google_amtype TEXT,
    amtype      TEXT,
    lat         REAL     NOT NULL,
    lng         REAL     NOT NULL,
    address     TEXT,
    municipality    TEXT,
    province    TEXT,
    country     TEXT,
    FOREIGN KEY(google_pid) REFERENCES Places(placeid)
        ON DELETE SET NULL
        ON UPDATE CASCADE
);

WITH CTE AS
( 
    SELECT P.placeid AS placeid, P.name AS name, P.address AS address, 
           P.lat AS lat, P.lng AS lng,
           P.country AS country,
           P.website AS website,
           A1.Geometry AS adm1_geometry, A1.NAME_1 AS province,
           A2.Geometry AS adm2_geometry, A2.NAME_2 AS municipality
    FROM NICA.Places AS P 
    CROSS JOIN NIC_adm1_shp AS A1
    JOIN NIC_adm2_shp AS A2 ON A1.NAME_1 = A2.NAME_1
    WHERE P.country = 'Nicaragua' AND
          Within(MakePoint(P.lng, P.lat, 4326), A1.Geometry) = 1 AND 
          Within(MakePoint(P.lng, P.lat, 4326), A2.Geometry) = 1
) 
INSERT INTO NICA.Health_Facilities(google_pid, name, lat, lng, address, municipality,
                                province, country, website, google_amtype)
   SELECT CTE.placeid, CTE.name,
           CTE.lat, CTE.lng,
           CTE.address,
           CTE.municipality,
           CTE.province,
           CTE.country,
           CTE.website,
           AM.amtype
    FROM CTE
    JOIN (  SELECT placeid, amtype, COUNT(*)
            FROM NICA.AmenityTypes
            WHERE amtype IN ('hospital', 'pharmacy', 'dentist', 'doctor', 'physiotherapist')
            GROUP BY placeid
            HAVING COUNT(*) = 1
         ) AS AM
    ON CTE.placeid = AM.placeid;
    
UPDATE 'NICA'.'Health_Facilities'
SET amtype = 
         CASE
           WHEN lower(name) GLOB '*centro de salud*' OR
                lower(name) GLOB '*healt* center' THEN 'health centre'
           WHEN lower(name) GLOB '*puesto de salud*' THEN 'health post'
           WHEN lower(name) GLOB '*odon*ologica*' OR
                lower(name) GLOB '*dental*' THEN 'dentist'
         END
WHERE google_amtype = 'hospital';     

UPDATE NICA."Health_Facilities"
SET amtype = 'maternity home'
WHERE name GLOB '*casa materna*';

UPDATE NICA."Health_Facilities"
SET amtype = 'profamilia'
WHERE lower(name) GLOB '*profamilia';

UPDATE NICA.Health_Facilities
SET amtype = 
       CASE
           WHEN lower(name) GLOB '*laborator?* cl?nic*' THEN 'laboratory'
           WHEN lower(name) GLOB 'cl?nic* perinatal' OR
                lower(name) GLOB '*perinatal cl?nic*' THEN 'maternal home'
           WHEN lower(name) GLOB '*centro m?dico*' OR
                lower(name) GLOB '*medic* center*' THEN 'health centre'
       END
WHERE google_amtype = 'hospital' AND amtype IS NULL;

UPDATE NICA.Health_Facilities
SET amtype = 'clinic'
WHERE lower(name) GLOB '*cl?nic*' AND google_amtype = 'hospital' AND 
      amtype IS NULL;
      
UPDATE NICA.Health_Facilities
SET amtype = google_amtype
WHERE amtype IS NULL;

CREATE VIEW IF NOT EXISTS NICA.View_CountAmtypeByName AS
   SELECT amtype, COUNT(*) AS num
   FROM NICA.Health_Facilities
   GROUP BY amtype
   ORDER BY amtype;
   
END;