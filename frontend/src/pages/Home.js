import {useState,useEffect} from 'react'

import { applicationVersionUpdate } from '../components/Functions';
import Flashbar from "@cloudscape-design/components/flashbar";
import CustomHeader from "../components/Header";
import ContentLayout from '@cloudscape-design/components/content-layout';
import { configuration } from './Configs';

import Button from "@cloudscape-design/components/button";
import Container from "@cloudscape-design/components/container";
import Header from "@cloudscape-design/components/header";
import Box from "@cloudscape-design/components/box";
import ColumnLayout from "@cloudscape-design/components/column-layout";
import Badge from "@cloudscape-design/components/badge";
import AppLayout from '@cloudscape-design/components/app-layout';

import '@aws-amplify/ui-react/styles.css';


function Home() {
  
  //-- Application Version
  const [versionMessage, setVersionMessage] = useState([]);
  
  
  //-- Call API to App Version
   async function gatherVersion (){

        //-- Application Update
        var appVersionObject = await applicationVersionUpdate({ codeId : "dbwcmp", moduleId: "home"} );
        
        if (appVersionObject.release > configuration["apps-settings"]["release"] ){
          setVersionMessage([
                              {
                                type: "info",
                                content: "New Application version is available, new features and modules will improve application capabilities and user experience.",
                                dismissible: true,
                                dismissLabel: "Dismiss message",
                                onDismiss: () => setVersionMessage([]),
                                id: "message_1"
                              }
          ]);
      
        }
        
   }
   
   
   useEffect(() => {
        gatherVersion();
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, []);
  
  return (
      
    <div>
      <CustomHeader/>
      <AppLayout
            toolsHide
            navigationHide
            contentType="default"
            content={
              <ContentLayout 
                          header = {
                                   <>
                                      <Flashbar items={versionMessage} />
                                      <br/>
                                      <Header variant="h1">
                                              Welcome to {configuration["apps-settings"]["application-title"]}
                                      </Header>
                                      <br/>
                                      <Box fontSize="heading-s">
                                          Speed up and automate AWS resource tagging for The AWS Migration Acceleration Program (MAP).
                                      </Box>
                                      <br/>
                                      <Box fontSize="heading-s">
                                          {configuration["apps-settings"]["application-title"]} is an automation tool offering you specify tag and values  
                                          and apply those configurations to AWS resources in different accounts and regions. It aims to provide you with complete visibility into how your tags are applied to your AWS resources.
                                          
                                    
                                      </Box>
                                      <br/>
                                  </>

                                }
                                
                    >
                  
                    <div>
                    <ColumnLayout columns={2} >
                      
                            <div>
                                <Container
                                      header = {
                                        <Header variant="h2">
                                          How it works?
                                        </Header>
                                        
                                      }
                                  >
                                        <div>
                                                  <Badge>1</Badge> Automate tagging process for AWS Resources.
                                                  <br/>
                                                  <br/>
                                                  <Badge>2</Badge> Speed up resource tagging.
                                                  <br/>
                                                  <br/>
                                                  <Badge>3</Badge> Consolidate all tagging information into centralized dashboard.
                                                  <br/>
                                                  <br/>
                                                  <Badge>4</Badge> Control taging resources for AWS MAP Program.
                                        </div>
                              </Container>
                              
                          </div>
                    
                          <div>
                                    <Container
                                          header = {
                                            <Header variant="h2">
                                              Getting Started
                                            </Header>
                                            
                                          }
                                      >
                                            <div>
                                              <Box variant="p">
                                                  Start tagging process for your AWS resources.
                                              </Box>
                                              <br/>
                                              <Button variant="primary" href="/dashboard/" >Get Started</Button>
                                              <br/>
                                              <br/>
                                            </div>
                                  </Container>
                                  
                          </div>
                              
                          
                          </ColumnLayout>
                          <br/>
                          <Container
                                      header = {
                                        <Header variant="h2">
                                          Use cases
                                        </Header>
                                        
                                      }
                                  >
                                         <ColumnLayout columns={1} variant="text-grid">
                                              <div>
                                                <Header variant="h3">
                                                  Manage tagging process
                                                </Header>
                                                <Box variant="p">
                                                  MAP Tagger Solution is powerful tool to automatically manage tags to help better manage your AWS resources needed by Migration Accelaration Program.
                                                </Box>
                                              </div>
                                              <div>
                                                <Header variant="h3">
                                                  Visualize global tagging process
                                                </Header>
                                                <Box variant="p">
                                                  It will provide you capabilities to manage those configurations globally for different accounts and regions. 
                                                </Box>
                                              </div>
                                              
                                              
                                        </ColumnLayout>
                              </Container>
                              
                          </div>
                      </ContentLayout>
            }
          />
    </div>
    
  );
}

export default Home;
