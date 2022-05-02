import { Injectable } from '@angular/core';
import { IBaseMessage } from 'ogre-router/dist/tsc/models/ogre';
import { Observable, Subject } from 'rxjs';
import { filter } from 'rxjs/operators';

@Injectable({
  providedIn: 'root'
})
export class MessageService {

  private _onMessage: Subject<IBaseMessage> = new Subject<IBaseMessage>();
  private recievedMessages: {
    [userId: string]: IBaseMessage[]
  } = {};

  constructor() {
    console.log('message service constructed');
  }

  nextMessage(message: IBaseMessage): void {
    if (this.recievedMessages[message.source]) {
      this.recievedMessages[message.source].push(message);
    } else {
      this.recievedMessages[message.source] = [message];
    }
    this._onMessage.next(message);
  }

  onMessage(): Observable<IBaseMessage> {
    return this._onMessage;
  }

  onMessageById(userId: string): Observable<IBaseMessage> {
    return this._onMessage.pipe(filter(item => item.source === userId));
  }

  getMessagesById(userId: string): IBaseMessage[] {
    if (this.recievedMessages[userId]) {
      return this.recievedMessages[userId];
    } else {
      this.recievedMessages[userId] = [];
      return [];
    }
  }
}
