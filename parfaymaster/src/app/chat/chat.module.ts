import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';

import { ChatRoutingModule } from './chat-routing.module';
import { ChatComponent } from './chat.component';
import { PrivateComponent } from './private/private.component';
import { SharedModule } from '../shared/shared.module';
import { MaterialModule } from '../material.module';


@NgModule({
  declarations: [
    ChatComponent,
    PrivateComponent
  ],
  imports: [
    CommonModule,
    ChatRoutingModule,
    SharedModule,
    MaterialModule
  ]
})
export class ChatModule { }
