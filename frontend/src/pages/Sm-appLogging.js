import { useState,useEffect,useRef } from 'react'
import Axios from 'axios'
import { configuration, SideMainLayoutHeader,SideMainLayoutMenu } from './Configs';

import { applicationVersionUpdate, gatherLocalVersion } from '../components/Functions';
import { createLabelFunction } from '../components/Functions';

import SideNavigation from '@cloudscape-design/components/side-navigation';
import AppLayout from '@cloudscape-design/components/app-layout';

import Flashbar from "@cloudscape-design/components/flashbar";
import Container from "@cloudscape-design/components/container";
import Select from "@cloudscape-design/components/select";


import SpaceBetween from "@cloudscape-design/components/space-between";
import Button from "@cloudscape-design/components/button";
import CustomHeader from "../components/Header";
import CustomTable02 from "../components/Table02";

import Header from "@cloudscape-design/components/header";
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



function Application() {
  
    //-- Application Version
    const [messages, setMessages] = useState([]);
    const [logFilesList, setLogFilesList] = useState([]);
    const [selectedOption,setSelectedOption] = useState({});
    var logFileName = useRef("");
  
    //-- Add Header Cognito Token
    Axios.defaults.headers.common['x-csrf-token'] = sessionStorage.getItem("x-csrf-token");
    Axios.defaults.headers.common['x-token-cognito'] = sessionStorage.getItem("x-token-cognito");
    Axios.defaults.withCredentials = true;
    
    
    //-- Table Messages
    const columnsTable =  [
                  {id: 'message', header: 'Messages',cell: item => item,ariaLabel: createLabelFunction('message'),sortingField: 'message',}
    ];
    
    const visibleContent = ['message'];
    
   
   //-- Gather Import Process
   async function gatherApplicationLogfiles (){
      
      try {
        
            var api_url = configuration["apps-settings"]["api-url"];
            var params = {};
            Axios.get(`${api_url}/api/aws/tagger/logging/list/files`,{
                      params: params, 
                  }).then((data)=>{
                    console.log(data);
                    var logFiles = [];
                   
                    data.data.logFiles.forEach(file => {
                        logFiles.push({
                                      label: file,
                                      value: file
                                     });
                    });
                
                    setLogFilesList(logFiles);
                    if (logFiles.length > 0) {
                        setSelectedOption(logFiles[0]);
                        logFileName.current=logFiles[0].value;
                    }
                         
                                                    
              })
              .catch((err) => {
                  console.log('Timeout API Call : /api/aws/tagger/logging/list/files' );
                  console.log(err);
              });
            
        }
        catch{
        
          console.log('Timeout API error : /api/aws/application/update/status');                  
          
        }
    
    }
    
    function onClickViewLogFile(){
      
        try {
        
            setMessages([]);
            var api_url = configuration["apps-settings"]["api-url"];
            var params = { fileName : logFileName.current };
            Axios.get(`${api_url}/api/aws/tagger/logging/get/content`,{
                      params: params, 
                  }).then((data)=>{
                     console.log(data);
                     setMessages(data.data.logContent);
              })
              .catch((err) => {
                  console.log('Timeout API Call : /api/aws/tagger/logging/get/content' );
                  console.log(err);
              });
            
        }
        catch{
        
          console.log('Timeout API error : /api/aws/tagger/logging/get/content');                  
          
        }
            

    }
    
   
    useEffect(() => {
        gatherApplicationLogfiles();
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, []);
    
    
    
    
    
  return (
    <div>
        <CustomHeader/>
        <AppLayout
            disableContentPaddings
            toolsHide
            navigation={<SideNavigation activeHref={"/logging/"} items={SideMainLayoutMenu} header={SideMainLayoutHeader} />}
            contentType="default"
            content={
                
                <div style={{"padding" : "2em"}}>
                    <Container header={<Header variant="h2" description="To view the application logfile, click View LogFile button to fetch content file.">
                                            Application Logger
                                          </Header>
                                      } 
                      >
                        <CustomTable02
                                columnsTable={columnsTable}
                                visibleContent={visibleContent}
                                dataset={messages}
                                title={"Messages"}
                                description={""}
                                pageSize={20}
                                onSelectionItem={( item ) => {
                                  }
                                }
                                extendedTableProperties = {
                                    { variant : "borderless" }
                                    
                                }
                                tableActions = {
                                        <SpaceBetween
                                            direction="horizontal"
                                            size="xs"
                                          >
                                          <Select
                                                  selectedOption={selectedOption}
                                                  onChange={({ detail }) =>{
                                                        setSelectedOption(detail.selectedOption);
                                                        logFileName.current=detail.selectedOption.value;
                                                    }
                                                  }
                                                  options={logFilesList}
                                                  filteringType="auto"
                                          />
                                          <Button variant="primary" onClick={ onClickViewLogFile }>View Logfile</Button>
                                        </SpaceBetween>
                                }
                                
                        />
                    </Container>
                </div>
            }
            disableContentHeaderOverlap={true}
            headerSelector="#h" 
        />
                      
    </div>
  );
}

export default Application;

