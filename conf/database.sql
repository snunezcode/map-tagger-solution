
//-- DDL Section

CREATE DATABASE db;
 
USE db;
 
CREATE TABLE tbTaggerRecords( 
   id int NOT NULL AUTO_INCREMENT,
   process_id varchar(32),
   account_id varchar(32),
   region varchar(32),
   service varchar(16),
   type varchar(1),
   resource_name varchar(64),
   tag_key varchar(32),
   tag_value varchar(32),
   creation_date varchar(32),
   tag_list text,
   timestamp varchar(32),
   PRIMARY KEY (id)
);


