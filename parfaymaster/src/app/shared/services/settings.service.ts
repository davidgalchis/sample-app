import { Injectable, Renderer2, RendererFactory2 } from '@angular/core';
import { BehaviorSubject, Observable } from 'rxjs';

export interface IPreferences {
  theme: 'light' | 'dark'
}

@Injectable({
  providedIn: 'root'
})
export class SettingsService {

  private renderer: Renderer2;

  private prefrences: IPreferences = {
    theme: 'dark'
  }
  private preferencesSubject: BehaviorSubject<IPreferences>;

  constructor(
    private rendererFactory: RendererFactory2
  ) {
    this.renderer = this.rendererFactory.createRenderer(null, null);

    this.prefrences = JSON.parse(localStorage.getItem('preferences') || JSON.stringify(this.prefrences));
    this.preferencesSubject = new BehaviorSubject<IPreferences>(this.prefrences);
    this.preferencesSubject.subscribe(prefrences => {
      localStorage.setItem('preferences', JSON.stringify(prefrences));
      this.applyTheme(prefrences.theme);
    });
  }

  public getPreferences(): IPreferences {
    return this.prefrences;
  }
  public observePreferences(): Observable<IPreferences> {
    return this.preferencesSubject.asObservable();
  }

  public lightTheme(): void {
    this.prefrences.theme = 'light';
    this.preferencesSubject.next(this.prefrences);
  }

  public darkTheme(): void {
    this.prefrences.theme = 'dark';
    this.preferencesSubject.next(this.prefrences);
  }

  private applyTheme(theme: 'light' | 'dark') {
    if (theme === 'light') {
      this.renderer.addClass(document.body, 'parfay-light-theme');
      this.renderer.removeClass(document.body, 'parfay-dark-theme');
    } else {
      this.renderer.addClass(document.body, 'parfay-dark-theme');
      this.renderer.removeClass(document.body, 'parfay-light-theme');
    }
  }
}
