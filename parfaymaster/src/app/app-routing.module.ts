import { NgModule } from '@angular/core';
import { RouterModule, Routes } from '@angular/router';

const routes: Routes = [
  {
    path: '',
    redirectTo: 'chat',
    pathMatch: 'full'
  },
  { 
    path: 'chat', 
    loadChildren: () => import('./chat/chat.module').then(m => m.ChatModule) 
  },
  { 
    path: 'settings',
    loadChildren: () => import('./settings/settings.module').then(m => m.SettingsModule) 
  }
];

@NgModule({
  imports: [RouterModule.forRoot(routes)],
  exports: [RouterModule]
})
export class AppRoutingModule { }
