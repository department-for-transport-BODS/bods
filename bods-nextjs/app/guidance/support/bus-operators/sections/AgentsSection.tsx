/**
 * Agents Section
 * Source: transit_odp/guidance/templates/guidance/bus_operators/agents.html
 */

export function AgentsSection() {
  return (
    <>
      <h2 data-qa="agents-header" className="govuk-heading-l">Agents</h2>
      <p className="govuk-body">
        Agents are defined as people outside the operator's organisation that can publish
        data on behalf of an operator. Most commonly, these will be local transport
        authorities. It is expected that operators will have contracts establishing the
        services and expectations with agents, prior to allocating them as an agent on
        this service.
      </p>

      <h2 data-qa="removing-agents-header" className="govuk-heading-l">Allocating and removing agents</h2>
      <p className="govuk-body">
        Please ensure operators and agents have support agreements and contracts in place
        prior to allocating agent users on this service.
      </p>
      <p className="govuk-body">
        An operator's admin user can allocate agents to publish data to the service, by
        going to my account and selecting user management.
      </p>

      <h2 className="govuk-heading-l">Agent users</h2>
      <p className="govuk-body">
        Please ensure the operator invites all the agent users to be agents for their
        organisation, this may be multiple emails for local authority. Alternatively,
        agents may wish to use a functional mailbox for the agent user account. However,
        this will limit people that can log in at once to those with the same external
        IP address.
      </p>
      <p className="govuk-body">
        An operator's admin user can allocate agents to publish data to the service,
        by going to my account and selecting user management.
      </p>

      <h2 className="govuk-heading-l">Agents can</h2>
      <ul className="govuk-list govuk-list--bullet">
        <li>Publish all types of data</li>
        <li>Update the National Operator Codes (NOC) associated with the operator the service</li>
        <li>Remove themselves as an agent for an operator</li>
      </ul>

      <h2 className="govuk-heading-l">Agents cannot</h2>
      <ul className="govuk-list govuk-list--bullet">
        <li>Take over the legal obligation to provide data to BODS; they can only publish data</li>
        <li>Add users to an operator's organisation</li>
      </ul>

      <h2 className="govuk-heading-l">Notification emails</h2>
      <p className="govuk-body">
        Notification emails will be sent to both the admin user and agent when:
      </p>
      <ul className="govuk-list govuk-list--bullet">
        <li>Any user publishes data</li>
        <li>An agent accepts or rejects the invite to the operator's organisation</li>
        <li>An agent or operator removes the agent at a later date</li>
        <li>National Operator Codes are edited</li>
      </ul>
    </>
  );
}


