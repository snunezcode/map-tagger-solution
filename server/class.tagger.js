const exec = require('child_process').exec;
const fs = require('fs');

//--#############
//--############# CLASS : classTaggerProcess
//--#############


class classTaggerProcess {

        logging = [];
        status = "non-started"
        applicationDirectory = "/aws/apps/agent/";
        scriptCommand = "sudo -u ec2-user sh /aws/apps/agent/run.sh"
        constructor(object) { 
            
        }
        
        //-- StartUpdate
        startProcess(module,type,message) { 
            
            this.status = "started";
            this.logging = [];
            const objectShell = exec(this.scriptCommand);
            objectShell.stdout.on('data', (data)=>{
                    if (data !== "") {
                        this.logging.unshift({ timestamp : new Date().toLocaleString(), message : data });
                        this.status = "in-progress";
                    }
            });
            
            objectShell.stderr.on('data', (data)=>{
                    if (data !== "") {
                        this.logging.unshift({ timestamp : new Date().toLocaleString(), message : data });
                        this.status = "in-progress";
                    }
            });
            
            objectShell.on('close', (code) => {
              this.status = "completed";
            });
            
        }
        
        
        //-- Get Update Status
        getUpdateLog(){
            
            return this.logging;
            
        }
        
        
        //-- Get log files
        getLoggingFiles(){
            var files = [];
            try {
                fs.readdirSync(this.applicationDirectory).forEach(file => {
                  if (file.slice(-4) === ".log")
                    files.push(file);
                });
            } catch (err) {
                console.error(err);
            }
            return files;
        }
        
        //-- Read log fiile
        getLogfileContent(fileName){
            var logContent = [];
            try {
                logContent = fs.readFileSync(this.applicationDirectory + fileName, 'utf8').split('\n');
            } catch (err) {
                console.error(err);
            }
            
            return logContent;
            
        }
        
        
}

module.exports = { classTaggerProcess };