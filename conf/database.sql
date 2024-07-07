CREATE DATABASE db;
 
USE db;

CREATE TABLE tbTaggingProcess( 
   id int NOT NULL AUTO_INCREMENT,
   process_id varchar(32),
   inventory_status varchar(12),
   inventory_start_date varchar(32),
   inventory_end_date varchar(32),
   inventory_items_total int,
   inventory_items_completed int,
   inventory_message varchar(64),
   tagging_status varchar(12),
   tagging_start_date varchar(32),
   tagging_end_date varchar(32),
   tagging_message varchar(64),
   tagging_items_total int,
   tagging_items_completed int,
   configuration text,
   PRIMARY KEY (id)
);

 
CREATE TABLE tbTaggingRecords( 
   id int NOT NULL AUTO_INCREMENT,
   process_id varchar(32),
   account_id varchar(32),
   region varchar(32),
   service varchar(16),
   type varchar(1),
   identifier varchar(64),
   resource_name varchar(64),
   arn varchar(256),
   tag_key varchar(32),
   tag_value varchar(32),
   creation_date varchar(32),
   tag_list text,
   timestamp varchar(32),
   PRIMARY KEY (id)
);

