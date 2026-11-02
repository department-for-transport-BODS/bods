import { validateEditDescription } from './edit-description';
import { EDIT_DESCRIPTION_ERRORS } from './messages';

describe('validateEditDescription', () => {
  it.each([
    {
      name: 'returns no errors when both descriptions are provided',
      input: { description: 'A description', shortDescription: 'Short' },
      expected: {},
    },
    {
      name: 'flags whitespace-only descriptions as missing',
      input: { description: '  ', shortDescription: '\n' },
      expected: {
        description: EDIT_DESCRIPTION_ERRORS.description,
        shortDescription: EDIT_DESCRIPTION_ERRORS.shortDescription,
      },
    },
    {
      name: 'flags only the missing short description',
      input: { description: 'A description', shortDescription: '' },
      expected: { shortDescription: EDIT_DESCRIPTION_ERRORS.shortDescription },
    },
  ])('$name', ({ input, expected }) => {
    expect(validateEditDescription(input)).toEqual(expected);
  });
});
