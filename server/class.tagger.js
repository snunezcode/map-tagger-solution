const exec = require('child_process').exec;
const fs = require('fs');

//--#############
//--############# CLASS : classTaggerProcess
//--#############


class classTaggerProcess {

        logging = [];
        status = "non-started"
        applicationDirectory = "/aws/apps/agent/";
        pluginDirectory = "/aws/apps/agent/plugins/";
        scriptCommand = "sudo -u ec2-user sh /aws/apps/agent/run.sh "
        constructor(object) { 
            
        }
        
        //-- StartUpdate
        startProcess(processType, processId) { 
            
            this.status = "started";
            this.logging = [];
            const objectShell = exec(this.scriptCommand + processType +  " " + processId );
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
            return files.sort().reverse();
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
        
        
        //-- Get plugin list
        getPluginList(){
            var fileList = [];
            try {
                
                const files = fs.readdirSync(this.pluginDirectory);
                for (let file of files) {
                    if (file.substr(file.length - 3) == ".py"){
                        const fileInfo = fs.statSync(this.pluginDirectory + file);
                        fileList.push({ name: file, size : fileInfo.size, date : fileInfo.ctime });
                    }
                }
                return(fileList);
                
            } catch (err) {
                console.error(err);
            }
            
            return fileList;
            
        }
        
        
        //-- Delete plugin 
        deletePlugin(fileName){
            try {
                fs.unlinkSync(this.pluginDirectory + fileName);
            } catch (err) {
                console.error(err);
            }
            
        }
        
        
        //-- View plugin 
        viewPlugin(fileName){
            var fileContent = [];
            try {
                fileContent = fs.readFileSync(this.pluginDirectory + fileName, 'utf8').toString();
            } catch (err) {
                console.error(err);
            }
            return fileContent;
        }
        
        
}

module.exports = { classTaggerProcess };