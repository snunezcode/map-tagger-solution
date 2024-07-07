const { classDataStore, classConfiguration } = require('./class.core.js');
const { classApplicationUpdate } = require('./class.update.js');
const { classTaggerProcess } = require('./class.tagger.js');


var dataObjectStore = new classDataStore();
var taggerProcessObject = new classTaggerProcess();
var configurationObject = new classConfiguration();

const fs = require('fs');
const express = require("express");
const cors = require('cors');
const uuid = require('uuid');
var configData = JSON.parse(fs.readFileSync('./aws-exports.json'));

const app = express();
const port = configData.aws_api_port;

app.use(cors());
app.use(express.json())
                     

// API Protection
var cookieParser = require('cookie-parser')
var csrf = require('csurf')
var bodyParser = require('body-parser')
const csrfProtection = csrf({
  cookie: true,
});

app.use(bodyParser.json());
app.use(bodyParser.urlencoded({ extended: false }));
app.use(cookieParser());
app.use(csrfProtection);


// Security Variables
const crypto = require('crypto');
const jwt = require('jsonwebtoken');
var jwkToPem = require('jwk-to-pem');
var request = require('request');
var pems;
var issCognitoIdp = "https://cognito-idp." + configData.aws_region + ".amazonaws.com/" + configData.aws_cognito_user_pool_id;
var secretKey =  crypto.randomBytes(32).toString('hex')


//-- Application Update
var applicationUpdate = new classApplicationUpdate();


// Startup - Download PEMs Keys
gatherPemKeys(issCognitoIdp);


//--################################################################################################################
//--------------------------------------------  SECURITY 
//--################################################################################################################

//-- Generate new standard token
function generateToken(tokenData){
    const token = jwt.sign(tokenData, secretKey, { expiresIn: 60 * 60 * configData.aws_token_expiration });
    return token ;
};


//-- Verify standard token
const verifyToken = (token) => {

    try {
        const decoded = jwt.verify(token, secretKey);
        return {isValid : true, session_id: decoded.session_id};
    }
    catch (ex) { 
        return {isValid : false, session_id: ""};
    }

};

//-- Gather PEMs keys from Cognito
function gatherPemKeys(iss)
{

    if (!pems) {
        //Download the JWKs and save it as PEM
        return new Promise((resolve, reject) => {
                    request({
                       url: iss + '/.well-known/jwks.json',
                       json: true
                     }, function (error, response, body) {
                         
                        if (!error && response.statusCode === 200) {
                            pems = {};
                            var keys = body['keys'];
                            for(var i = 0; i < keys.length; i++) {
                                //Convert each key to PEM
                                var key_id = keys[i].kid;
                                var modulus = keys[i].n;
                                var exponent = keys[i].e;
                                var key_type = keys[i].kty;
                                var jwk = { kty: key_type, n: modulus, e: exponent};
                                var pem = jwkToPem(jwk);
                                pems[key_id] = pem;
                            }
                        } else {
                            //Unable to download JWKs, fail the call
                            console.log("error");
                        }
                        
                        resolve(body);
                        
                    });
        });
        
        } 
    
    
}


//-- Validate Cognito Token
function verifyTokenCognito(token) {

   try {
        //Fail if the token is not jwt
        var decodedJwt = jwt.decode(token, {complete: true});
        if (!decodedJwt) {
            console.log("Not a valid JWT token");
            return {isValid : false, session_id: ""};
        }
        
        
        if (decodedJwt.payload.iss != issCognitoIdp) {
            console.log("invalid issuer");
            return {isValid : false, session_id: ""};
        }
        
        //Reject the jwt if it's not an 'Access Token'
        if (decodedJwt.payload.token_use != 'access') {
            console.log("Not an access token");
            return {isValid : false, session_id: ""};
        }
    
        //Get the kid from the token and retrieve corresponding PEM
        var kid = decodedJwt.header.kid;
        var pem = pems[kid];
        if (!pem) {
            console.log('Invalid access token');
            return {isValid : false, session_id: ""};
        }

        const decoded = jwt.verify(token, pem, { issuer: issCognitoIdp });
        return {isValid : true, session_id: ""};
    }
    catch (ex) { 
        console.log("Unauthorized Token");
        return {isValid : false, session_id: ""};
    }
    
};



//--################################################################################################################
//--------------------------------------------  API GENERAL 
//--################################################################################################################


//--++ API : GENERAL : Get list of tagger process
app.get("/api/aws/tagger/process/list", async (req, res) => {

    // Token Validation
    var cognitoToken = verifyTokenCognito(req.headers['x-token-cognito']);

    if (cognitoToken.isValid === false)
        return res.status(511).send({ data: [], message : "Token is invalid"});
 
    const params = req.query;

    try {
        
        var records = await dataObjectStore.getMasterRecords();
        var summaryResources = await dataObjectStore.getSummaryResources();
        var summaryServices = await dataObjectStore.getSummaryServices();

        res.status(200).send({ csrfToken: req.csrfToken(), records : records, summaryResources : summaryResources, summaryServices : summaryServices  })
        
    } catch(error) {
        console.log(error);
        res.status(401).send({ Clusters : []});
    }
    
});




//--++ API : GENERAL : Get list of tagger process with details
app.get("/api/aws/tagger/process/details", async (req, res) => {

    // Token Validation
    var cognitoToken = verifyTokenCognito(req.headers['x-token-cognito']);

    if (cognitoToken.isValid === false)
        return res.status(511).send({ data: [], message : "Token is invalid"});
 
    const params = req.query;

    try {
        
        var records = await dataObjectStore.getChildRecords({ process_id : params.process_id, type : params.type });
        var summary = await dataObjectStore.getResourceSummaryByProcess({ process_id : params.process_id });
        res.status(200).send({ csrfToken: req.csrfToken(), records : records, summary : summary })
        
    } catch(error) {
        console.log(error);
        res.status(401).send({ Clusters : []});
    }
    
});



//--++ API : GENERAL : Update resource action
app.get("/api/aws/tagger/process/resource/update", async (req, res) => {

    // Token Validation
    var cognitoToken = verifyTokenCognito(req.headers['x-token-cognito']);

    if (cognitoToken.isValid === false)
        return res.status(511).send({ data: [], message : "Token is invalid"});
 
    const params = req.query;

    try {
        
        await dataObjectStore.updateResourceAction({ process_id : params.process_id, id : params.id, type : params.type });
        res.status(200).send({ csrfToken: req.csrfToken(), action : "success"  });
        
    } catch(error) {
        console.log(error);
        res.status(401).send({ csrfToken: req.csrfToken(), action : "failed"  });
    }
    
});


//--++ API : GENERAL : Inventory Process - Start
app.get("/api/aws/tagger/process/start", async (req, res) => {

    // Token Validation
    var cognitoToken = verifyTokenCognito(req.headers['x-token-cognito']);
    
    const params = req.query;
    console.log(params);
    if (cognitoToken.isValid === false)
        return res.status(511).send({ data: [], message : "Token is invalid"});
    
    try {
        
        taggerProcessObject.startProcess(params.processType, params.processId);
        res.status(200).send({ csrfToken: req.csrfToken(), status : "started"} )
        
    } catch(error) {
        console.log(error);
        res.status(401).send({});
    }
});





//--++ API : GENERAL : Tagger Process - Status
app.get("/api/aws/tagger/process/collection/status", async (req, res) => {

    // Token Validation
    var cognitoToken = verifyTokenCognito(req.headers['x-token-cognito']);

    if (cognitoToken.isValid === false)
        return res.status(511).send({ data: [], message : "Token is invalid"});
 
    try {
        
        res.status(200).send({ csrfToken: req.csrfToken(), status : taggerProcessObject.status, messages : taggerProcessObject.getUpdateLog() } )
        
    } catch(error) {
        console.log(error);
        res.status(401).send({});
    }
    
});


//--++ API : GENERAL : Tagger Process - Progress
app.get("/api/aws/tagger/process/collection/progress", async (req, res) => {

    // Token Validation
    var cognitoToken = verifyTokenCognito(req.headers['x-token-cognito']);

    const params = req.query;
    
    if (cognitoToken.isValid === false)
        return res.status(511).send({ data: [], message : "Token is invalid"});
 
    try {
        
        res.status(200).send({ csrfToken: req.csrfToken(), status : await dataObjectStore.getProgress({ processId : params.processId } ) } )
        
    } catch(error) {
        console.log(error);
        res.status(401).send({});
    }
    
});


//--++ API : GENERAL : Application Update - Start
app.get("/api/aws/application/update/start", async (req, res) => {

    // Token Validation
    var cognitoToken = verifyTokenCognito(req.headers['x-token-cognito']);

    if (cognitoToken.isValid === false)
        return res.status(511).send({ data: [], message : "Token is invalid"});
 
    
    try {
        
        applicationUpdate.startUpdate();
        res.status(200).send({ csrfToken: req.csrfToken(), status : "started"} )
        
    } catch(error) {
        console.log(error);
        res.status(401).send({});
    }
    
});


//--++ API : GENERAL : Application Update - Status
app.get("/api/aws/application/update/status", async (req, res) => {

    // Token Validation
    var cognitoToken = verifyTokenCognito(req.headers['x-token-cognito']);

    if (cognitoToken.isValid === false)
        return res.status(511).send({ data: [], message : "Token is invalid"});
 
    try {
        
        res.status(200).send({ csrfToken: req.csrfToken(), status : applicationUpdate.status, messages : applicationUpdate.getUpdateLog() } )
        
    } catch(error) {
        console.log(error);
        res.status(401).send({});
    }
    
});




//--++ API : GENERAL : Get Configuration
app.get("/api/aws/tagger/configuration/get", async (req, res) => {

    // Token Validation
    var cognitoToken = verifyTokenCognito(req.headers['x-token-cognito']);

    if (cognitoToken.isValid === false)
        return res.status(511).send({ data: [], message : "Token is invalid"});
 
    try {
        
        
        configurationObject.read()
          .then((jsonData) => {
            res.status(200).send({ csrfToken: req.csrfToken(), configuration : jsonData } )
          })
          .catch((error) => {
            console.error('Error:', error);
        });
          
        
        
    } catch(error) {
        console.log(error);
        res.status(401).send({});
    }
    
});



//--++ API : GENERAL : Save Configuration
app.post("/api/aws/tagger/configuration/save", async (req, res) => {


    // Token Validation
    var cognitoToken = verifyTokenCognito(req.headers['x-token-cognito']);

    if (cognitoToken.isValid === false)
        return res.status(511).send({ data: [], message : "Token is invalid"});
 
    var params = req.body.params;
    try {
        configurationObject.write(params.configuration)
          .then(() => {
            res.status(200).send({ csrfToken: req.csrfToken(), state : "success" } )
          })
          .catch((error) => {
            console.error('Error:', error);
            res.status(200).send({ csrfToken: req.csrfToken(), state : "error" } )
        });
         
    } catch(error) {
        console.log(error);
        res.status(401).send({});
    }
    
    
});


//--++ API : GENERAL : Tagger Process - List log files
app.get("/api/aws/tagger/logging/list/files", async (req, res) => {

    // Token Validation
    var cognitoToken = verifyTokenCognito(req.headers['x-token-cognito']);

    if (cognitoToken.isValid === false)
        return res.status(511).send({ data: [], message : "Token is invalid"});
    
    try {
        
        var logFiles = taggerProcessObject.getLoggingFiles();
        res.status(200).send({ csrfToken: req.csrfToken(), logFiles : logFiles } )
        
    } catch(error) {
        console.log(error);
        res.status(401).send({});
    }
});


//--++ API : GENERAL : Tagger Process - Get logfile content
app.get("/api/aws/tagger/logging/get/content", async (req, res) => {

    // Token Validation
    var cognitoToken = verifyTokenCognito(req.headers['x-token-cognito']);

    if (cognitoToken.isValid === false)
        return res.status(511).send({ data: [], message : "Token is invalid"});
    
    const params = req.query;
    
    try {
        
        var logContent = taggerProcessObject.getLogfileContent(params.fileName);
        res.status(200).send({ csrfToken: req.csrfToken(), logContent : logContent } );
        
    } catch(error) {
        console.log(error);
        res.status(401).send({});
    }
});

//--################################################################################################################
//--------------------------------------------  CORE
//--################################################################################################################


app.listen(port, () => {
  console.log(`App listening on port ${port}`);
});


