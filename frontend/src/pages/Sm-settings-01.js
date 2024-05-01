import {useState,useEffect,useRef} from 'react'
import { createSearchParams } from "react-router-dom";
import Axios from 'axios'
import { configuration, SideMainLayoutHeader,SideMainLayoutMenu, breadCrumbs } from './Configs';
import { applicationVersionUpdate, getMatchesCountText, createLabelFunction, paginationLabels, pageSizePreference, collectionPreferencesProps, EmptyState, customFormatNumberShort, customFormatNumberLong, customFormatNumber } from '../components/Functions';

import { useCollection } from '@cloudscape-design/collection-hooks';
import {CollectionPreferences,Pagination } from '@cloudscape-design/components';
import TextFilter from "@cloudscape-design/components/text-filter";

import CustomHeader from "../components/Header";
import AppLayout from "@cloudscape-design/components/app-layout";
import SideNavigation from '@cloudscape-design/components/side-navigation';

import Flashbar from "@cloudscape-design/components/flashbar";
import { StatusIndicator } from '@cloudscape-design/components';
import SpaceBetween from "@cloudscape-design/components/space-between";
import Button from "@cloudscape-design/components/button";
import Table from "@cloudscape-design/components/table";
import Header from "@cloudscape-design/components/header";
import Box from "@cloudscape-design/components/box";
import ColumnLayout from "@cloudscape-design/components/column-layout";
import Container from "@cloudscape-design/components/container";
import FormField from "@cloudscape-design/components/form-field";
import Input from "@cloudscape-design/components/input";
import Textarea from "@cloudscape-design/components/textarea";
import Form from "@cloudscape-design/components/form";
import { SplitPanel } from '@cloudscape-design/components';
import '@aws-amplify/ui-react/styles.css';


export const splitPanelI18nStrings: SplitPanelProps.I18nStrings = {
  preferencesTitle: 'Split panel preferences',
  preferencesPositionLabel: 'Split panel position',
  preferencesPositionDescription: 'Choose the default split panel position for the service.',
  preferencesPositionSide: 'Side',
  preferencesPositionBottom: 'Bottom',
  preferencesConfirm: 'Confirm',
  preferencesCancel: 'Cancel',
  closeButtonAriaLabel: 'Close panel',
  openButtonAriaLabel: 'Open panel',
  resizeHandleAriaLabel: 'Resize split panel',
};




//-- Encryption
var CryptoJS = require("crypto-js");

function Application() {
    
    //-- Application Messages
    const [applicationMessage, setApplicationMessage] = useState([]);
  
    var currentProcessId = useRef("");
    
    //-- Add Header Cognito Token
    Axios.defaults.headers.common['x-token-cognito'] = sessionStorage.getItem("x-token-cognito");
    Axios.defaults.withCredentials = true;
    
    const [txtAccountsField, setTxtAccountsField] = useState("");
   
    //-- Handle Click Events
    async function gatherConfiguration (){
            try{
            const { data } = await Axios.get(`${configuration["apps-settings"]["api-url"]}/api/aws/tagger/configuration/get`);
            sessionStorage.setItem("x-csrf-token", data.csrfToken );
            sessionStorage.setItem("x-csrf-token", data.csrfToken );
            setTxtAccountsField(JSON.stringify(data['configuration'],undefined,4));
            console.log(data);
        }
        catch{
          console.log('Timeout API error : /api/aws/tagger/configuration/get');                  
        }
    };
    
    async function saveConfiguration (){
            try{
            
                var params = { configuration : JSON.parse(txtAccountsField) };
                const { data } = await Axios.get(`${configuration["apps-settings"]["api-url"]}/api/aws/tagger/configuration/save`,{ params : params });
                console.log(data);
                if (data.state == "success"){
                  
                      setApplicationMessage([
                                        {
                                          type: "info",
                                          content: "Configuration has been saved, click Refresh to load configuration.",
                                          dismissible: true,
                                          dismissLabel: "Dismiss message",
                                          onDismiss: () => setApplicationMessage([]),
                                          id: "message_1"
                                        }
                      ]);
                      
                } else {
                  
                  setApplicationMessage([
                                        {
                                          type: "error",
                                          content: "Configuration has an error, verify JSON structure and try again.",
                                          dismissible: true,
                                          dismissLabel: "Dismiss message",
                                          onDismiss: () => setApplicationMessage([]),
                                          id: "message_1"
                                        }
                      ]);
                  
                }
        }
        catch{
              setApplicationMessage([
                                        {
                                          type: "error",
                                          content: "Configuration has an error, verify JSON structure and try again.",
                                          dismissible: true,
                                          dismissLabel: "Dismiss message",
                                          onDismiss: () => setApplicationMessage([]),
                                          id: "message_1"
                                        }
              ]);
          console.log('Timeout API error : /api/aws/tagger/configuration/save');                  
        }
    };
    
    
    
    
    
    function convertToObjects(tagListString) {
      try {
        // Remove the outer parentheses and square brackets from the string
        const innerString = tagListString.slice(2, -2);
        console.log(innerString);
        // Parse the inner string as a JSON array
        const jsonArray = JSON.parse(`[${innerString}]`);
    
        // Return the parsed array
        return jsonArray;
      } catch (error) {
        console.error('Error converting string to JSON objects:', error);
        return null;
      }
    }

    
    
    //-- Init Function
    // eslint-disable-next-line
    useEffect(() => {
        gatherConfiguration();
        
    }, []);
    
    
  return (
    <div style={{"background-color": "#f2f3f3"}}>
        <CustomHeader/>
        <AppLayout
            headerSelector="#h"
            toolsHide
            disableContentPaddings={true}
            breadCrumbs={breadCrumbs}
            navigation={<SideNavigation items={SideMainLayoutMenu} header={SideMainLayoutHeader} activeHref={"/settings/"} />}
            contentType="table"
            content={
                      <div style={{"padding" : "1em"}}>
                          <Flashbar items={applicationMessage} />
                          <br/>
                          <Container
                            header={
                                      <Header
                                        variant="h2"
                                      >
                                        Settings
                                      </Header>
                                    }
                          >
                           <table style={{"width":"100%"}}>
                                <tr>  
                                    <td valign="middle" style={{"width":"50%", "padding-right": "2em", "text-align": "center"}}>  
                                        <FormField
                                          label="Process Configuration"
                                          description="Parameters must be introduced using the following JSON format"
                                        >
                                            <Textarea
                                              placeholder='{ "accounts" : [{ "id" : "123456789", "regions" : ["us-east-1","us-west-2"] } ] }'
                                              onChange={({ detail }) => setTxtAccountsField(detail.value)}
                                              value={txtAccountsField}
                                              rows={30}
                                            />
                                            <br/>
                                            <Box float="right">
                                            <SpaceBetween
                                              direction="horizontal"
                                              size="xs"
                                            >
                                              <Button onClick={gatherConfiguration} variant={"secondary"}>Refresh</Button>
                                              <Button onClick={saveConfiguration} variant={"primary"}>Save</Button>
                                            </SpaceBetween>
                                        </Box>    
                                        </FormField>    
                                    </td>
                                </tr>
                                
                            </table>
                          </Container>
                          
                  </div>
                
            }
          />
        
    </div>
  );
}

export default Application;
