import { NgModule } from '@angular/core';
import { RouterModule, Routes } from '@angular/router';
import { ChatComponent } from './chat.component';
import { PrivateComponent } from './private/private.component';

const routes: Routes = [
  { 
    path: '', 
    component: ChatComponent,
    children: [
      {
        path: '',
        redirectTo: 'private',
        pathMatch: 'full'
      },
      { 
        path: 'private', 
        component: PrivateComponent
      }
    ]
  }
];

@NgModule({
  imports: [RouterModule.forChild(routes)],
  exports: [RouterModule]
})
export class ChatRoutingModule { }
