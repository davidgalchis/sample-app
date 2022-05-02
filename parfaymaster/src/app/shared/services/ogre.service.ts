import { Injectable } from '@angular/core';
import { Ogre, User } from 'ogre-router';
import { IBaseMessage } from 'ogre-router/dist/tsc/models/ogre';
import { BehaviorSubject, Subject } from 'rxjs';
import { MessageService } from './message.service';

@Injectable({
  providedIn: 'root'
})
export class OgreService {

  ogre: Ogre;

  private _onPeerlistUpdated: Subject<{ id: string; alias: string;}[]> = new Subject<{ id: string; alias: string;}[]>();
  private _onTargetUserUpdated: BehaviorSubject<{ id: string; alias: string;} | undefined> = new BehaviorSubject<{ id: string; alias: string;} | undefined>(undefined);

  constructor(private messageService: MessageService) {
    this.ogre = new Ogre({
      // signalingAddress: 'ws://localhost:3000'
      signalingAddress: 'wss://parfay-example-server.herokuapp.com'
    });
    const subscription = this.ogre.onUserLoaded().subscribe(user => {
      if (user) {
        this.ogre.observeMessages().subscribe((message: IBaseMessage) => {
          this.messageService.nextMessage(message);
        });
    
        this.ogre.observePeerList().subscribe(list => {
          this._onPeerlistUpdated.next(list.filter(_user => _user.id !== user.id));
        });
        
        subscription.unsubscribe();
      }
    });
  }

  onPeerlistUpdated(): Subject<{ id: string; alias: string;}[]> {
    return this._onPeerlistUpdated;
  }

  async getUser(): Promise<User> {
    return new Promise(resolve => {
      this.ogre.onUserLoaded().subscribe(user => {
        if (user) resolve(user);
      });
    });
  }

  selectTargetPeer(user: { id: string; alias: string; }): void {
    this.ogre.selectTargetPeer(user);
    this._onTargetUserUpdated.next(user);
  }

  onTargetUserUpdated(): BehaviorSubject<{ id: string; alias: string;} | undefined>{
    return this._onTargetUserUpdated;
  }

  sendMessage(message: string): void {
    console.log('sending message', message);
    this.ogre.sendMessage(message);
  }

}
