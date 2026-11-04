/**
 * Organisation Selection Page
 *
 * Allows publishers to select which organisation to work with
 */

"use client";

import { useState, useEffect, useCallback } from "react";
import Link from "next/link";
import { ProtectedRoute } from "@/components/auth/ProtectedRoute";
import { Breadcrumbs } from "@/components/shared/Breadcrumbs";
import { getPaginated } from "@/lib/api-client";
import { useAuth } from "@/hooks/useAuth";
import { useRouter, useSearchParams } from "next/navigation";
import { HOSTS, publishAppPath } from "@/config/client";

interface Organisation {
  id: number;
  name: string;
  short_name?: string;
}

function SelectOrg() {
  const [orgs, setOrgs] = useState<Organisation[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const { user } = useAuth();
  const router = useRouter();
  const searchParams = useSearchParams();

  const selectedDataType = searchParams.get("dataType");

  const isValidDataType =
    selectedDataType === "timetable" ||
    selectedDataType === "avl" ||
    selectedDataType === "fares";
  const organisationHref = useCallback(
    (orgId: number) =>
      publishAppPath(
        `/org/${orgId}/dataset${isValidDataType ? `/${selectedDataType}` : ""}`,
      ),
    [isValidDataType, selectedDataType],
  );

  useEffect(() => {
    const loadOrganisations = async () => {
      try {
        const data = await getPaginated<Organisation>(
          "/api/publish/organisations/",
        );

        if (data.results.length === 1 && user?.is_single_org_user) {
          const orgId = data.results[0].id;
          router.push(organisationHref(orgId));
          return;
        }

        setOrgs(data.results);
      } catch (err) {
        console.error("Failed to load organisations", err);
      } finally {
        setIsLoading(false);
      }
    };

    loadOrganisations();
  }, [organisationHref, router, user?.is_single_org_user]);

  const renderOrganisations = () => {
    if (isLoading) {
      return <p className="govuk-body">Loading organisations...</p>;
    }

    if (orgs.length === 0) {
      return (
        <>
          <p className="govuk-body-l">
            You don’t have any operators yet to act as an agent on behalf of.
            Please go to My Account section to set-up an operator
          </p>
          <Link
            href={publishAppPath("/account")}
            role="button"
            draggable="false"
            className="govuk-button govuk-button--start"
          >
            Go to My Account
            <svg
              className="govuk-button__start-icon"
              xmlns="http://www.w3.org/2000/svg"
              width="17.5"
              height="19"
              viewBox="0 0 33 40"
              role="presentation"
              focusable="false"
            >
              <path fill="currentColor" d="M0 0h13l20 20-20 20H0l20-20z" />
            </svg>
          </Link>
        </>
      );
    }

    return (
      <ul className="govuk-list">
        {orgs.map((org) => (
          <li key={org.id}>
            <Link
              className="govuk-link govuk-!-font-weight-bold govuk-!-font-size-19"
              href={organisationHref(org.id)}
            >
              {org.name}
            </Link>
          </li>
        ))}
      </ul>
    );
  };

  return (
    <>
      <div className="govuk-width-container">
        <div className="govuk-main-wrapper govuk-!-padding-top-0 govuk-!-padding-bottom-0">
          <Breadcrumbs
            items={[
              { label: "Bus Open Data Service", href: HOSTS.www },
              { label: "Publish Bus Open Data", href: HOSTS.publish },
              {
                label: "Operator Dashboard",
                href: publishAppPath("/org"),
                current: true,
              },
            ]}
          />
        </div>
      </div>

      <div className="govuk-width-container">
        <div className="govuk-main-wrapper">
          <div className="govuk-grid-row">
            <div className="govuk-grid-column-two-thirds">
              <h1 className="govuk-heading-xl">Operator Dashboard</h1>

              {orgs.length > 0 && (
                <p className="govuk-body-l">
                  Choose an operator to view or publish data
                </p>
              )}

              {renderOrganisations()}
            </div>
          </div>
        </div>
      </div>
    </>
  );
}

export default function SelectOrgPage() {
  return (
    <ProtectedRoute>
      <SelectOrg />
    </ProtectedRoute>
  );
}
