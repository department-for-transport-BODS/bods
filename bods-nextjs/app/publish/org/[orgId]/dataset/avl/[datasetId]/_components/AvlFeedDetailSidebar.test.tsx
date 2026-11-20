import { render, screen } from '@testing-library/react';
import { AvlFeedDetailSidebar } from './AvlFeedDetailSidebar';

describe('AvlFeedDetailSidebar', () => {
  it.each([
    ['View our guidelines here', /\/guidance\/operator-requirements\/$/],
    ['AVL feed compliance guidance', /\/guidance\/operator-requirements\/\?section=dataquality$/],
    [
      'AVL to Timetables matching guidance',
      /\/guidance\/operator-requirements\/\?section=dataquality#avl-to-timetable-matching$/,
    ],
  ])('links "%s" to the same guidance URL as Django', (name, href) => {
    render(<AvlFeedDetailSidebar />);

    expect(screen.getByRole('link', { name }).getAttribute('href')).toMatch(href);
  });
});
