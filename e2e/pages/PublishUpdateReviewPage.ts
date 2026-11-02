import { expect, Page } from '@playwright/test';

export type UpdateDatasetType = 'timetable' | 'fares';

/** Django's update journeys use Comment / Update; the first-publish journey uses Describe / Provide. */
export type PublishJourney = 'update' | 'publish';

const STEPS: Record<PublishJourney, string[]> = {
  update: ['1. Comment', '2. Update', '3. Review and publish'],
  publish: ['1. Describe data', '2. Provide data', '3. Review and publish'],
};

export class PublishUpdateReviewPage {
  constructor(private readonly page: Page) {}

  private datasetPath(type: UpdateDatasetType, orgId: string, datasetId: string): string {
    return `/publish/org/${orgId}/dataset/${type}/${datasetId}`;
  }

  async navigateToReview(type: UpdateDatasetType, orgId: string, datasetId: string): Promise<void> {
    await this.page.goto(`${this.datasetPath(type, orgId, datasetId)}/update/review`, {
      waitUntil: 'domcontentloaded',
    });
  }

  /** `update/review/update` for an update draft, `review/update` for a first-publish draft. */
  async navigateToModify(
    type: UpdateDatasetType,
    orgId: string,
    datasetId: string,
    journey: PublishJourney = 'update',
  ): Promise<void> {
    const suffix = journey === 'update' ? 'update/review/update' : 'review/update';
    await this.page.goto(`${this.datasetPath(type, orgId, datasetId)}/${suffix}`, {
      waitUntil: 'domcontentloaded',
    });
  }

  async navigateToUpdate(type: UpdateDatasetType, orgId: string, datasetId: string): Promise<void> {
    await this.page.goto(`${this.datasetPath(type, orgId, datasetId)}/update`, { waitUntil: 'domcontentloaded' });
  }

  /** `success` after a first publish, `update/success` after publishing an update. */
  async navigateToSuccess(
    type: UpdateDatasetType,
    orgId: string,
    datasetId: string,
    journey: PublishJourney,
  ): Promise<void> {
    const suffix = journey === 'update' ? 'update/success' : 'success';
    await this.page.goto(`${this.datasetPath(type, orgId, datasetId)}/${suffix}`, { waitUntil: 'domcontentloaded' });
  }

  async assertUpdateStepper(journey: PublishJourney = 'update'): Promise<void> {
    for (const step of STEPS[journey]) {
      await expect(this.page.locator('.govuk-breadcrumbs').getByText(step, { exact: true })).toBeVisible();
    }
  }

  private get commentField() {
    return this.page.getByRole('textbox', { name: 'Comment on data set updates' });
  }

  async assertCommentStep(): Promise<void> {
    await expect(
      this.page.getByRole('heading', { level: 1, name: 'Provide a comment on what has been updated' }),
    ).toBeVisible();
    await this.assertUpdateStepper('update');
    await expect(this.commentField).toHaveAttribute('name', 'comment-comment');
  }

  async continueWithoutComment(): Promise<void> {
    await this.page.getByRole('button', { name: 'Continue' }).click();
    await expect(this.page.getByRole('link', { name: 'Enter a comment in the box below' })).toHaveAttribute(
      'href',
      '#id_comment-comment',
    );
  }

  async continueWithComment(comment: string): Promise<void> {
    await this.commentField.fill(comment);
    await this.page.getByRole('button', { name: 'Continue' }).click();
    await expect(this.page.getByRole('group', { name: 'Update your published data set' })).toBeVisible();
  }

  async assertSuccessPanel(journey: PublishJourney): Promise<void> {
    const verb = journey === 'update' ? 'updated' : 'published';
    await expect(
      this.page.getByRole('heading', { level: 1, name: `Your data set has been successfully ${verb}` }),
    ).toBeVisible();
    await expect(this.page).toHaveTitle(journey === 'update' ? 'Data set updated' : 'Data set published');
  }

  async assertReviewLoaded(datasetName: string): Promise<void> {
    await expect(this.page.getByRole('heading', { level: 1, name: 'Review and publish' })).toBeVisible();
    await this.assertUpdateStepper();
    await expect(this.page.getByRole('heading', { level: 2, name: datasetName })).toBeVisible();
  }

  async assertTimetablePropertyTable(orgId: string, datasetId: string): Promise<void> {
    const table = this.page.locator('table.dataset-property-table');
    for (const header of ['Name', 'Description', 'Short description', 'Status', 'Owner', 'Last updated']) {
      await expect(table.getByRole('rowheader', { name: header, exact: true })).toHaveCount(1);
    }
    const editLinks = table.getByRole('link', { name: /^Edit/ });
    await expect(editLinks).toHaveCount(2);
    for (const link of await editLinks.all()) {
      await expect(link).toHaveAttribute(
        'href',
        new RegExp(`/org/${orgId}/dataset/timetable/${datasetId}/revision-edit/$`),
      );
    }
    await expect(
      this.page.getByRole('checkbox', {
        name: 'I have reviewed the data quality report and wish to publish my data',
      }),
    ).toHaveAttribute('name', 'consent');
    await expect(this.page.getByRole('button', { name: 'Publish data' })).toBeDisabled();
  }

  async assertFaresConsentAndEditLinks(orgId: string, datasetId: string): Promise<void> {
    const consent = this.page.getByRole('checkbox', {
      name: 'I have reviewed the submission and wish to publish my data',
    });
    await expect(consent).toHaveAttribute('name', 'consent');
    await expect(consent).toHaveAttribute('id', 'id_consent');

    const editLinks = this.page.getByRole('link', { name: 'Edit', exact: true });
    await expect(editLinks).toHaveCount(2);
    for (const link of await editLinks.all()) {
      await expect(link).toHaveAttribute('href', new RegExp(`/org/${orgId}/dataset/fares/${datasetId}/revision-edit/$`));
    }

    await expect(this.page.getByRole('link', { name: 'View our guidelines here' })).toHaveAttribute(
      'href',
      /\/guidance\/operator-requirements$/,
    );
    await expect(this.page.getByRole('link', { name: 'Contact support desk' })).toHaveAttribute('href', /\/contact$/);
  }

  private get urlRadio() {
    return this.page.locator('#url_link-conditional-radio');
  }

  private get fileRadio() {
    return this.page.locator('#upload_file-conditional-radio');
  }

  private get urlConditional() {
    return this.page.locator('#url_link-conditional');
  }

  private get fileConditional() {
    return this.page.locator('#upload_file-conditional');
  }

  async assertModifyHeading(): Promise<void> {
    await expect(
      this.page.getByRole('heading', { level: 1, name: 'Choose how to provide your data set' }),
    ).toBeVisible();
  }

  async assertModifyForm(journey: PublishJourney = 'update'): Promise<void> {
    await this.assertModifyHeading();
    await this.assertUpdateStepper(journey);
    await expect(this.page.locator('[data-module="app-radio-accordion"] [data-module="govuk-radios"]')).toHaveCount(1);
    await expect(this.urlRadio).toHaveAttribute('name', 'selected_item');
    await expect(this.urlRadio).toHaveAttribute('value', 'url_link-conditional');
    await expect(this.fileRadio).toHaveAttribute('name', 'selected_item');
    await expect(this.fileRadio).toHaveAttribute('value', 'upload_file-conditional');
    await expect(this.urlConditional).toHaveClass(/govuk-radios__conditional--hidden/);
    await expect(this.fileConditional).toHaveClass(/govuk-radios__conditional--hidden/);
  }

  async chooseUrl(): Promise<void> {
    await this.urlRadio.check();
    await expect(this.urlConditional).not.toHaveClass(/govuk-radios__conditional--hidden/);
    await expect(this.page.locator('input[name="url_link"]')).toBeVisible();
  }

  async chooseFile(): Promise<void> {
    await this.fileRadio.check();
    await expect(this.fileConditional).not.toHaveClass(/govuk-radios__conditional--hidden/);
    await expect(this.urlConditional).toHaveClass(/govuk-radios__conditional--hidden/);
    await expect(this.page.locator('input[name="upload_file"]')).toBeVisible();
  }

  async cancel(): Promise<void> {
    await this.page.getByRole('button', { name: 'Cancel', exact: true }).click();
  }

  /** Confirm returns to the review page the modify page came from. */
  async assertCancelStep(
    type: UpdateDatasetType,
    orgId: string,
    datasetId: string,
    journey: PublishJourney = 'update',
  ): Promise<void> {
    await expect(
      this.page.getByRole('heading', { level: 1, name: 'Would you like to cancel updating this data set?' }),
    ).toBeVisible();
    await expect(this.page.getByText('Any changes you have made so far will not be saved.')).toBeVisible();
    const reviewSuffix = journey === 'update' ? 'update/review/' : 'review/';
    await expect(this.page.getByRole('button', { name: 'Confirm' })).toHaveAttribute(
      'href',
      new RegExp(`/org/${orgId}/dataset/${type}/${datasetId}/${reviewSuffix}$`),
    );
  }

  async backFromCancel(): Promise<void> {
    await this.page.getByRole('button', { name: 'Back' }).click();
  }
}
