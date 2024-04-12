//-- Filesystem Object
const fs = require('fs');

//-- Logging Object
const { classLogging } = require('./class.logging.js');

//-- MySQL Object
const mysql = require('mysql2/promise')


//--#############
//--############# FUNCTIONS                                                                                        
//--#############


function replaceParameterValues(str, obj) {
  var re = /\{(.+?)\}/g;
  return str.replace(re, function(_,m){return obj[m]});
}


//--#############
//--############# CLASS : classDataStore                                                                                               
//--#############

class classDataStore {

        //-- Looging
        #objLog = new classLogging({ name : "classDataStore", instance : "generic" });
        
        objectConnection = {};
        #connection = {};
        
        ///-- Database Queries
        #sql_statement_tagger_process_master = `select a.process_id, b.accounts,c.regions, a.total as total_resources, a.total_type_1 as total_resources_tagged, a.total_type_2 as total_resources_added,a.total_type_3 as total_resources_skipped
                                                from
                                                (
                                                   select process_id, count(*) as total, sum( case when type=1 then 1 else 0 end) as total_type_1,sum( case when type=2 then 1 else 0 end) as total_type_2,sum( case when type=3 then 1 else 0 end) as total_type_3 from tbTaggerRecords group by process_id
                                                ) a,
                                                (
                                                   select process_id, GROUP_CONCAT(account_id) as accounts from (select process_id, account_id from tbTaggerRecords group by process_id,account_id) a group by process_id
                                                ) b,
                                                (
                                                   select process_id, GROUP_CONCAT(region) as regions from (select process_id, region from tbTaggerRecords group by process_id,region) a group by process_id
                                                ) c
                                                where 
                                                a.process_id=b.process_id
                                                and
                                                a.process_id=c.process_id
                                                order by 
                                                a.process_id desc`;
                                                
        #sql_statement_tagger_process_details = "select *, case when type=1 then 'tagged' when type=2 then 'added' when type=3 then 'skipped' end as type_desc from tbTaggerRecords where process_id = ?";
        
        #sql_statement_summary_resources = `select a.process_id, a.total_type_1 as total_resources_tagged, a.total_type_2 as total_resources_added, a.total_type_3 as total_resources_skipped
                                            from
                                            (
                                               select process_id, count(*) as total, sum( case when type=1 then 1 else 0 end) as total_type_1,sum( case when type=2 then 1 else 0 end) as total_type_2,sum( case when type=3 then 1 else 0 end) as total_type_3 from tbTaggerRecords group by process_id
                                            ) a
                                            order by 
                                            a.process_id desc
                                            limit 10`;
        #sql_statement_summary_service = `select 
                                                a.process_id, a.service, count(*) as total 
                                          from 
                                                tbTaggerRecords a,
                                                (select process_id from tbTaggerRecords group by process_id order by process_id desc limit 10) b
                                          where
                                                a.process_id = b.process_id
                                          group by a.process_id, a.service order by a.process_id desc`;
        

        //-- Constructor method
        constructor() { 
                this.objectConnection.host = "localhost";
                this.objectConnection.port = "3306";
                this.objectConnection.user = "admin";
                this.objectConnection.password = "";
                this.objectConnection.database = "db";
                this.#openConnection();
        }
          
        
        //-- Open Connection
        async #openConnection() { 
            
            
                try {
                    
                                this.#objLog.write("#openConnection","info","MySQL Instance Connected : ");
                            
                                this.#connection = new  mysql.createPool({
                                                                            host: this.objectConnection.host,
                                                                            user: this.objectConnection.user,
                                                                            password: this.objectConnection.password,
                                                                            database: this.objectConnection.database,
                                                                            port: this.objectConnection.port,
                                                                            connectionLimit:2,
                                                                            socketPath: '/var/lib/mysql/mysql.sock'
                                                                            });
                                                                                    
                                
                                
                                this.#connection.on('error', (err, client) => {
                                            console.log(err);
                                            this.#objLog.write("#openConnection","err",err);
                                            
                                });
                                
                                var command = await this.#connection.query('SELECT @@hostname as value');
                               
                }
                catch(err){
                    this.#objLog.write("#openConnection","err",err);
                }
            

        }
        
        connect() { 
            this.#openConnection();
        }
        
        
        //-- Close Connection
        async #closeConnection() { 
            try {
                this.#objLog.write("#closeConnection","info", "Disconnection completed : " + this.objectConnection.host );
                    this.#connection.end();
            }
            catch(err){
                    this.#objLog.write("#closeConnection","err", String(err) + "-" + this.objectConnection.host );
            }
            
        }
        
        //-- Close Connection
        disconnect() { 
            this.#closeConnection();
        }
    
        async getMasterRecords(){
            var command = await this.#connection.query(this.#sql_statement_tagger_process_master);
            return command[0];
        }
        
        
        async getChildRecords(object){
            var parameters = [object.process_id];
            var command = await this.#connection.query(this.#sql_statement_tagger_process_details,parameters);
            return command[0];
        }
         
         
         
        async getSummaryResources(){
            
            var result = { resourceTagged : [], resourceAdded : [], resourceSkipped : [] };
            var command = await this.#connection.query(this.#sql_statement_summary_resources);
            try {
                command[0].forEach(item => {
                        result.resourceTagged.push({ x : item.process_id , y : parseFloat(item.total_resources_tagged) });
                        result.resourceAdded.push({ x : item.process_id , y : parseFloat(item.total_resources_added) });
                        result.resourceSkipped.push({ x : item.process_id , y : parseFloat(item.total_resources_skipped) });
                });
                
            }
            catch(err){
                    this.#objLog.write("getSummaryResources","err", String(err) + "-" + this.objectConnection.host );
            }
            
            return result;
        } 
        
        
        async getSummaryServices(){
            
            var result = [];
            var services = [];
            var command = await this.#connection.query(this.#sql_statement_summary_service);
            try {
                
                
                command[0].forEach(item => {
                        
                        if (!(item.service in services ))    
                            services[item.service] = [];
                        services[item.service].push({ x : item.process_id , y : parseFloat(item.total) });
                        
                });
                
                for (let service of Object.keys(services)) {
                    result.push({ title : service, type : "bar", data : services[service] });
                }
                
            }
            catch(err){
                    this.#objLog.write("getSummaryResources","err", String(err) + "-" + this.objectConnection.host );
            }
            
            
            return result;
            
        } 
          
}

//--#############
//--############# CLASS : classConfiguration                                                                                                
//--#############


class classConfiguration {

        #filePath = 'configuration.json';
        constructor(object) { 
            
        }
        
        read() {
          return new Promise((resolve, reject) => {
            fs.readFile(this.#filePath, 'utf8', (err, data) => {
              if (err) {
                reject(err);
              } else {
                try {
                  const jsonData = JSON.parse(data);
                  resolve(jsonData);
                } catch (parseError) {
                  reject(parseError);
                }
              }
            });
          });
        }
        
        
        write(data) {
          return new Promise((resolve, reject) => {
            const jsonData = JSON.stringify(data, null, 4); // Pretty print with indentation level 2
            fs.writeFile(this.#filePath, jsonData, 'utf8', (err) => {
              if (err) {
                reject(err);
              } else {
                resolve();
              }
            });
          });
        }
        
}


module.exports = { classDataStore, classConfiguration };



                