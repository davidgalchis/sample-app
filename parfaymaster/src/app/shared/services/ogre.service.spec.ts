import { TestBed } from '@angular/core/testing';

import { OgreService } from './ogre.service';

describe('OgreService', () => {
  let service: OgreService;

  beforeEach(() => {
    TestBed.configureTestingModule({});
    service = TestBed.inject(OgreService);
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });
});
