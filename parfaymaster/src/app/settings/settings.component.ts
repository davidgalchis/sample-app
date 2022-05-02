import { Component, OnInit, ViewChild } from '@angular/core';
import { MatAccordion } from '@angular/material/expansion';
import { MatSelectionListChange } from '@angular/material/list';
import { User } from 'ogre-router';
import { OgreService } from '../shared/services/ogre.service';
import { SettingsService } from '../shared/services/settings.service';

@Component({
  selector: 'app-settings',
  templateUrl: './settings.component.html',
  styleUrls: ['./settings.component.less']
})
export class SettingsComponent implements OnInit {

  @ViewChild(MatAccordion) accordion: MatAccordion;

  myUser: User;
  myUserName = '';
  myUserNumber = '';
  oldUserName = '';

  usingDarkTheme = true;

  constructor(
    private settingsService: SettingsService,
    private ogreService: OgreService
  ) {
    this.usingDarkTheme = this.settingsService.getPreferences().theme === 'dark';
  }

  async ngOnInit(): Promise<void> {
    console.log('settings component initialized');
    this.myUser = await this.ogreService.getUser();
    const splitUserId = this.myUser.alias.split('#');
    this.myUserName = splitUserId[0];
    this.oldUserName = splitUserId[0];
    this.myUserNumber = splitUserId[1];
  }

  themeRadioButtonChanged(event: MatSelectionListChange): void {
    if (event.options[0].value === 'light') this.lightTheme();
    if (event.options[0].value === 'dark') this.darkTheme();
  }

  saveProfileSettings(): void {
    this.saveProfileName();

  }

  private async saveProfileName(): Promise<void> {
    if (this.myUserName === this.oldUserName) return;
    const newUser = await this.ogreService.ogre.updateAlias(this.myUserName);
    console.log(newUser);
    // this.ogreService.ogre.user.setAlias(this.myUserName);
  }

  lightTheme(): void {
    this.settingsService.lightTheme();
  }

  darkTheme(): void {
    this.settingsService.darkTheme();
  }

}
