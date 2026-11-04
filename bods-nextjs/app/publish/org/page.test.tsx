import { render, screen } from "@testing-library/react";
import { waitFor } from "@testing-library/dom";
import SelectOrgPage from "./page";
import { getPaginated } from "@/lib/api-client";
import { useAuth } from "@/hooks/useAuth";
import { publishAppPath } from "@/config/client";
import { metadata as selectOrgMetadata } from "./page";

const mockPush = jest.fn();
const mockUseSearchParams = jest.fn();

jest.mock("next/navigation", () => ({
  useRouter: () => ({
    push: mockPush,
  }),
  useSearchParams: () => mockUseSearchParams(),
}));

jest.mock("@/components/auth/ProtectedRoute", () => ({
  ProtectedRoute: ({ children }: { children: React.ReactNode }) => (
    <>{children}</>
  ),
}));

jest.mock("@/hooks/useAuth", () => ({
  useAuth: jest.fn(),
}));

jest.mock("@/lib/api-client", () => ({
  getPaginated: jest.fn(),
}));

const dataTypeOptions = [
  {
    dataType: "timetable",
    expectedUrl: publishAppPath("/org/123/dataset/timetable"),
  },
  { dataType: "avl", expectedUrl: publishAppPath("/org/123/dataset/avl") },
  { dataType: "fares", expectedUrl: publishAppPath("/org/123/dataset/fares") },
];

describe("SelectOrgPage routing", () => {
  it("uses the Django page title", () => {
    expect(selectOrgMetadata.title).toBe("Operator Dashboard");
  });

  beforeEach(() => {
    jest.clearAllMocks();
    mockUseSearchParams.mockReturnValue(
      new URLSearchParams("dataType=timetable"),
    );
  });

  it("renders the operator dashboard heading, breadcrumb, and helper text", async () => {
    (useAuth as jest.Mock).mockReturnValue({
      user: { is_single_org_user: false, is_agent_user: true },
    });
    (getPaginated as jest.Mock).mockResolvedValue({
      results: [{ id: 123, name: "OrganisationOne" }],
    });

    render(<SelectOrgPage />);

    expect(
      screen.getByRole("heading", { name: "Operator Dashboard" }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("link", { name: "Operator Dashboard" }),
    ).toBeInTheDocument();
    expect(
      await screen.findByText("Choose an operator to view or publish data"),
    ).toBeInTheDocument();
  });

  it("matches Django when there are no organisations", async () => {
    (useAuth as jest.Mock).mockReturnValue({
      user: { is_single_org_user: false, is_agent_user: true },
    });
    (getPaginated as jest.Mock).mockResolvedValue({ results: [] });

    render(<SelectOrgPage />);

    expect(
      await screen.findByText(
        /You don’t have any operators yet to act as an agent on behalf of/,
      ),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: "Go to My Account" }),
    ).toHaveAttribute("href", publishAppPath("/account"));
  });

  it("keeps non-single organisation users on organisation selection", async () => {
    (useAuth as jest.Mock).mockReturnValue({
      user: {
        is_org_user: true,
        is_single_org_user: false,
        is_agent_user: false,
        organisation_id: 123,
      },
    });
    (getPaginated as jest.Mock).mockResolvedValue({
      results: [{ id: 123, name: "OrganisationOne" }],
    });

    render(<SelectOrgPage />);

    await waitFor(() =>
      expect(screen.getByText("OrganisationOne")).toBeInTheDocument(),
    );
    expect(mockPush).not.toHaveBeenCalled();
  });

  it.each(dataTypeOptions)(
    "routes single organisation users directly to their $dataType dataset page",
    async ({ dataType, expectedUrl }) => {
      mockUseSearchParams.mockReturnValue(
        new URLSearchParams(`dataType=${dataType}`),
      );
      (useAuth as jest.Mock).mockReturnValue({
        user: {
          is_org_user: true,
          is_single_org_user: true,
          is_agent_user: false,
          organisation_id: 123,
        },
      });
      (getPaginated as jest.Mock).mockResolvedValue({
        results: [{ id: 123, name: "OrganisationOne" }],
      });

      render(<SelectOrgPage />);

      await waitFor(() => expect(mockPush).toHaveBeenCalledWith(expectedUrl));
    },
  );

  it("defaults single organisation users directly to the dataset chooser page", async () => {
    mockUseSearchParams.mockReturnValue(new URLSearchParams());
    (useAuth as jest.Mock).mockReturnValue({
      user: {
        is_org_user: true,
        is_single_org_user: true,
        is_agent_user: false,
        organisation_id: 123,
      },
    });
    (getPaginated as jest.Mock).mockResolvedValue({
      results: [{ id: 123, name: "OrganisationOne" }],
    });

    render(<SelectOrgPage />);

    await waitFor(() =>
      expect(mockPush).toHaveBeenCalledWith(publishAppPath("/org/123/dataset")),
    );
  });

  it.each(dataTypeOptions)(
    "routes selected organisations to the requested $dataType dataset page",
    async ({ dataType, expectedUrl }) => {
      mockUseSearchParams.mockReturnValue(
        new URLSearchParams(`dataType=${dataType}`),
      );
      (useAuth as jest.Mock).mockReturnValue({
        user: {
          is_org_user: true,
          is_single_org_user: false,
          is_agent_user: false,
          organisation_id: 123,
        },
      });
      (getPaginated as jest.Mock).mockResolvedValue({
        results: [{ id: 123, name: "OrganisationOne" }],
      });

      render(<SelectOrgPage />);

      expect(
        await screen.findByRole("link", { name: "OrganisationOne" }),
      ).toHaveAttribute("href", expectedUrl);
    },
  );

  it("defaults selected organisations to the dataset chooser page", async () => {
    mockUseSearchParams.mockReturnValue(new URLSearchParams());
    (useAuth as jest.Mock).mockReturnValue({
      user: {
        is_org_user: true,
        is_single_org_user: false,
        is_agent_user: false,
        organisation_id: 123,
      },
    });
    (getPaginated as jest.Mock).mockResolvedValue({
      results: [{ id: 123, name: "OrganisationOne" }],
    });

    render(<SelectOrgPage />);

    expect(
      await screen.findByRole("link", { name: "OrganisationOne" }),
    ).toHaveAttribute("href", publishAppPath("/org/123/dataset"));
  });
});
