export type StepState = 'previous' | 'selected' | 'next';

export type PublishStep = {
  label: string;
  state: StepState;
};

type PublishStepperProps = {
  steps: PublishStep[];
};

export function PublishStepper({ steps }: PublishStepperProps) {
  return (
    <ol className="publish-stepper govuk-breadcrumbs__list" aria-label="Progress">
      {steps.map((step) => (
        <li
          key={step.label}
          className={`publish-stepper__item publish-stepper__item--${step.state}`}
        >
          {step.label}
        </li>
      ))}
    </ol>
  );
}
