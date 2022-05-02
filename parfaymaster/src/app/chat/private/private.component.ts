import { Component, ElementRef, OnInit, ViewChild } from '@angular/core';
import { IBaseMessage } from 'ogre-router/dist/tsc/models/ogre';
import { Subscription } from 'rxjs';
import { MessageService } from 'src/app/shared/services/message.service';
import { OgreService } from 'src/app/shared/services/ogre.service';

@Component({
  selector: 'app-private',
  templateUrl: './private.component.html',
  styleUrls: ['./private.component.less']
})
export class PrivateComponent implements OnInit {
  @ViewChild('messageBoxElement') messageBoxElement: ElementRef<any>;

  targetUser: { id: string; alias: string; } | undefined = undefined;
  displayedMessages: IBaseMessage[] = [];

  messagesSubscription: Subscription | undefined;

  constructor(
    private ogreService: OgreService,
    private messageService: MessageService
  ) { }

  ngOnInit(): void {
    this.ogreService.onTargetUserUpdated().subscribe(targetUser => {
      this.targetUser = targetUser;
      if (this.targetUser) {
        this.displayedMessages = this.messageService.getMessagesById(this.targetUser.id);
        if (this.messagesSubscription) this.messagesSubscription.unsubscribe();
        this.messagesSubscription = this.messageService.onMessageById(this.targetUser.id).subscribe(message => {
          this.displayedMessages.push(message);
          this.scrollMessageBoxDown();
        });
      }
    });
  }

  async sendMessage(messageBox: HTMLTextAreaElement): Promise<void> {
    const me = await this.ogreService.getUser();
    const thisMessage: IBaseMessage = {
      bare: true,
      message: messageBox.value,
      source: me.id,
      sourceAlias: me.alias,
      target: me.id,
      date: new Date()
    }
    this.displayedMessages.push(thisMessage);
    this.scrollMessageBoxDown();
    this.ogreService.sendMessage(messageBox.value);
    messageBox.value = '';
  }

  scrollMessageBoxDown(): void {
    setTimeout(() => {
      this.messageBoxElement.nativeElement.scrollTop = this.messageBoxElement.nativeElement.scrollHeight;
    });
  }

}
