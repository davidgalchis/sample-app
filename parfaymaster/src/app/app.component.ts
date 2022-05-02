import { Component, OnInit } from '@angular/core';
import { Router } from '@angular/router';
import { Ogre, User } from 'ogre-router';
import { MessageService } from './shared/services/message.service';
import { OgreService } from './shared/services/ogre.service';
import { SettingsService } from './shared/services/settings.service';


@Component({
  selector: 'app-root',
  templateUrl: './app.component.html',
  styleUrls: ['./app.component.less']
})
export class AppComponent implements OnInit {

  ogre: Ogre;
  userList: { id: string; alias: string; }[] = [];
  myUser: User;

  unreadMessages: { [id: string]: number } = {};
  targetUserId = '';

  constructor(
    private ogreService: OgreService,
    private settingsService: SettingsService,
    private messageService: MessageService,
    private router: Router
  ) { }

  async ngOnInit(): Promise<void> {
    this.ogreService.onPeerlistUpdated().subscribe(peerList => {
      this.userList = peerList;
    });
    this.myUser = await this.ogreService.getUser();
    this.messageService.onMessage().subscribe(message => {
      if (message.source !== this.targetUserId) {
        if (this.unreadMessages[message.source]) this.unreadMessages[message.source] += 1;
        else this.unreadMessages[message.source] = 1;
      }
    });
  }

  selectTargetUser(user: { id: string, alias: string }): void {
    this.targetUserId = user.id;
    this.unreadMessages[this.targetUserId] = 0;
    this.ogreService.selectTargetPeer(user);
  }

  selectSettings(): void {
    this.router.navigateByUrl('/settings');
    this.targetUserId = '';
  }

  // sendMessage(messageBox: HTMLTextAreaElement): void {
  //   this.ogre.sendMessage(messageBox.value);
  //   messageBox.value = '';
  // }

}
