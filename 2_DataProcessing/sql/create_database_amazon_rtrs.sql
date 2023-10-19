-- Welcome, here we create a RTRS_DB in SQLite!
-- This database will be useful for qgis applications and for creating relational data in sql

PRAGMA foreign_keys = ON;
-- Now FK is on

-- Step 1 Create Tables

CREATE TABLE FARM_BRANCHES (
	Latitude REAL,
	Longitude REAL,
	Name TEXT,
	Organization TEXT,
	Farm TEXT,
	State TEXT,
	City TEXT);


CREATE TABLE RTRS_BR (
	Organization TEXT,
	Name TEXT,
	Year INTEGER,
	Links TEXT,
	RegTag TEXT,
	Companies TEXT,
	Total_Production REAL,
	Issue_Date TEXT,
	Expiration_Date TEXT,
	Total_Farm_Area REAL,
	n_members INTEGER,
	Type TEXT,
	"1_1_criteria" TEXT,
	"1_2_criteria" TEXT,
	"1_3_criteria" TEXT,
	"2_1_criteria" TEXT,
	"2_2_criteria" TEXT,
	"2_3_criteria" TEXT,
	"2_4_criteria" TEXT,
	"2_5_criteria" TEXT,
	"3_1_criteria" TEXT,
	"3_2_criteria" TEXT,
	"3_3_criteria" TEXT,
	"3_4_criteria" TEXT,	
	"4_1_criteria" TEXT,
	"4_2_criteria" TEXT,
	"4_3_criteria" TEXT,
	"4_4_criteria" TEXT,
	"4_5_criteria" TEXT,
	"5_1_criteria" TEXT,
	"5_2_criteria" TEXT,
	"5_3_criteria" TEXT,
	"5_4_criteria" TEXT,
	"5_5_criteria" TEXT,
	"5_6_criteria" TEXT,
	"5_7_criteria" TEXT,
	"5_8_criteria" TEXT,
	"5_9_criteria" TEXT,
	"5_10_criteria" TEXT,
	"5_11_criteria" TEXT
);

-- Step 2 Load csv files into tables

.mode csv
.import /home/cleyton/ProjetosGit/msc_thesis_naea_ufpa/1_DataSource/csv_files/brazil_rtrs.csv RTRS_BR 

.mode csv
.import /home/cleyton/ProjetosGit/msc_thesis_naea_ufpa/2_DataProcessing/csv_result/farm_branches_update.csv FARM_BRANCHES 

-- Step 3 Delete 1st row, cause SQLite reads it wrong

DELETE FROM RTRS_BR WHERE rowid = 1;
DELETE FROM FARM_BRANCHES WHERE rowid = 1;

-- Step 3 Create Primary Key to Name

-- Create table NameIDMap and OrganizationIDMap

CREATE TABLE NameIDMap (
	NameID INTEGER PRIMARY KEY,
	Name TEXT
);

CREATE TABLE OrgIDMap (
	OrgID INTEGER PRIMARY KEY,
	Organization TEXT
);

-- Fill NameIDMap w/ unique values from Name RTRS_BR
INSERT INTO NameIDMap (Name)
SELECT DISTINCT Name
FROM RTRS_BR;

-- Fill OrgIDMap w/ unique values from Name RTRS_BR
INSERT INTO OrgIDMap (Organization)
SELECT DISTINCT Organization
FROM RTRS_BR;

-- Add NameID into RTRS_BR
ALTER TABLE RTRS_BR
ADD COLUMN NameID INTEGER;

-- Add NameId into FARM_BRANCHES
ALTER TABLE FARM_BRANCHES
ADD COLUMN NameID INTEGER;

-- Add OrgID into RTRS_BR
ALTER TABLE RTRS_BR
ADD COLUMN OrgID INTEGER;

-- Add OrgID into FARM_BRANCHES:
ALTER TABLE FARM_BRANCHES
ADD COLUMN OrgID INTEGER;

-- Update NameId w/ NameIDMap
UPDATE RTRS_BR
SET NameID = (SELECT NameID FROM NameIDMap WHERE NameIDMap.Name = RTRS_BR.Name);

-- Update OrgID w/ OrgIDMap
UPDATE RTRS_BR
SET OrgID = (SELECT OrgID FROM OrgIDMap WHERE OrgIDMap.Organization = RTRS_BR.Organization);

-- Update NameId w/ NameIDMap
UPDATE FARM_BRANCHES
SET NameID = (SELECT NameID FROM NameIDMap WHERE NameIDMap.Name = FARM_BRANCHES.Name);

-- Update OrgId w/ OrgIDMap
UPDATE FARM_BRANCHES
SET OrgID = (SELECT OrgID FROM OrgIDMap WHERE OrgIDMap.Organization = FARM_BRANCHES.Organization);

/*
Note that SQLite does not provide direct application of a foreign key to a table. This can only be done when a table is created. Therefore, despite consuming more programming effort, we will create a temporary table to solve this problem.
*/

CREATE TABLE FARM_BRANCHES_TEMP (
	Latitude REAL,
	Longitude REAL,
	Farm TEXT,
	State TEXT,
	City TEXT,
	NameID INTEGER,
	OrgID INTEGER,
	FOREIGN KEY (NameID) REFERENCES NameIDMap (NameID),
    	FOREIGN KEY (OrgID) REFERENCES OrgIDMap (OrgID)
);


CREATE TABLE RTRS_BR_TEMP (
	Year INTEGER,
	Links TEXT,
	RegTag TEXT,
	Companies TEXT,
	Total_Production REAL,
	Issue_Date TEXT,
	Expiration_Date TEXT,
	Total_Farm_Area REAL,
	n_members INTEGER,
	Type TEXT,
	"1_1_criteria" TEXT,
	"1_2_criteria" TEXT,
	"1_3_criteria" TEXT,
	"2_1_criteria" TEXT,
	"2_2_criteria" TEXT,
	"2_3_criteria" TEXT,
	"2_4_criteria" TEXT,
	"2_5_criteria" TEXT,
	"3_1_criteria" TEXT,
	"3_2_criteria" TEXT,
	"3_3_criteria" TEXT,
	"3_4_criteria" TEXT,	
	"4_1_criteria" TEXT,
	"4_2_criteria" TEXT,
	"4_3_criteria" TEXT,
	"4_4_criteria" TEXT,
	"4_5_criteria" TEXT,
	"5_1_criteria" TEXT,
	"5_2_criteria" TEXT,
	"5_3_criteria" TEXT,
	"5_4_criteria" TEXT,
	"5_5_criteria" TEXT,
	"5_6_criteria" TEXT,
	"5_7_criteria" TEXT,
	"5_8_criteria" TEXT,
	"5_9_criteria" TEXT,
	"5_10_criteria" TEXT,
	"5_11_criteria" TEXT,
	NameID INTEGER,
	OrgID INTEGER,
	FOREIGN KEY (NameID) REFERENCES NameIDMap (NameID),
    	FOREIGN KEY (OrgID) REFERENCES OrgIDMap (OrgID)
);

-- Copy data
INSERT INTO RTRS_BR_TEMP SELECT  
	Year,
	Links,
	RegTag,
	Companies,
	Total_Production,
	Issue_Date,
	Expiration_Date,
	Total_Farm_Area,
	n_members,
	Type,
	"1_1_criteria",
	"1_2_criteria",
	"1_3_criteria",
	"2_1_criteria",
	"2_2_criteria",
	"2_3_criteria",
	"2_4_criteria",
	"2_5_criteria",
	"3_1_criteria",
	"3_2_criteria",
	"3_3_criteria",
	"3_4_criteria",	
	"4_1_criteria",
	"4_2_criteria",
	"4_3_criteria",
	"4_4_criteria",
	"4_5_criteria",
	"5_1_criteria",
	"5_2_criteria",
	"5_3_criteria",
	"5_4_criteria",
	"5_5_criteria",
	"5_6_criteria",
	"5_7_criteria",
	"5_8_criteria",
	"5_9_criteria",
	"5_10_criteria",
	"5_11_criteria",
	NameID, 
	OrgID FROM RTRS_BR;
	
INSERT INTO FARM_BRANCHES_TEMP SELECT 
	Latitude,
	Longitude,
	Farm,
	State,
	City,
	NameID,
	OrgID FROM FARM_BRANCHES;

-- Drop Tables and rename new tables
DROP TABLE RTRS_BR;
ALTER TABLE RTRS_BR_TEMP RENAME TO RTRS_BR;

DROP TABLE FARM_BRANCHES;
ALTER TABLE FARM_BRANCHES_TEMP RENAME TO FARM_BRANCHES;


