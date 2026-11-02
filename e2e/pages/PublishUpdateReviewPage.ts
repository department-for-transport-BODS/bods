import { expect, Page } from '@playwright/test';

export type UpdateDatasetType = 'timetable' | 'fares';

const UPDATE_STEPS = ['1. Comment', '2. Update', '3. Review and publish'];

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

  async navigateToModify(type: UpdateDatasetType, orgId: string, datasetId: string): Promise<void> {
    await this.page.goto(`${this.datasetPath(type, orgId, datasetId)}/update/review/update`, {
      waitUntil: 'domcontentloaded',
    });
  }

  async assertUpdateStepper(): Promise<void> {
    for (const step of UPDATE_STEPS) {
      await expect(this.page.locator('.govuk-breadcrumbs').getByText(step, { exact: true })).toBeVisible();
    }
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

  async assertModifyForm(): Promise<void> {
    await this.assertModifyHeading();
    await this.assertUpdateStepper();
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

  async assertCancelStep(type: UpdateDatasetType, orgId: string, datasetId: string): Promise<void> {
    await expect(
      this.page.getByRole('heading', { level: 1, name: 'Would you like to cancel updating this data set?' }),
    ).toBeVisible();
    await expect(this.page.getByText('Any changes you have made so far will not be saved.')).toBeVisible();
    await expect(this.page.getByRole('button', { name: 'Confirm' })).toHaveAttribute(
      'href',
      new RegExp(`/org/${orgId}/dataset/${type}/${datasetId}/update/review/$`),
    );
  }

  async backFromCancel(): Promise<void> {
    await this.page.getByRole('button', { name: 'Back' }).click();
  }
}
