import { FARES_UPLOAD_FILE_ITEM_ID, validateFaresUploadStep } from './fares-publish';
import { FARES_PUBLISH_ERRORS } from './messages';

describe('validateFaresUploadStep', () => {
  it('rejects an empty file with the Django FileField message', () => {
    expect(
      validateFaresUploadStep({
        selectedItem: FARES_UPLOAD_FILE_ITEM_ID,
        urlLink: '',
        uploadFile: new File([], 'fares.xml'),
      }),
    ).toEqual({ uploadFile: FARES_PUBLISH_ERRORS.emptyUploadFile });
  });

  it('ignores the link when a file is selected', () => {
    expect(
      validateFaresUploadStep({
        selectedItem: FARES_UPLOAD_FILE_ITEM_ID,
        urlLink: '',
        uploadFile: new File(['<xml/>'], 'fares.xml'),
      }),
    ).toEqual({});
  });
});
