const exec = require('child_process').exec;

//--#############
//--############# CLASS : classTaggerProcess
//--#############


class classTaggerProcess {

        logging = [];
        status = "non-started"
        scriptCommand = "sudo -u ec2-user python3 /aws/apps/agent/agent.py"
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
        
        
}

module.exports = { classTaggerProcess };