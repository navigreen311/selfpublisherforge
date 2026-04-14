"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { toast } from "sonner";
import { useOrgSettings, useUpdateOrgSettings } from "../hooks";

const INDUSTRIES = [
  { value: "publishing", label: "Publishing" },
  { value: "media", label: "Media" },
  { value: "education", label: "Education" },
  { value: "other", label: "Other" },
];

const GENRES = [
  { value: "fiction", label: "Fiction" },
  { value: "nonfiction", label: "Nonfiction" },
  { value: "childrens", label: "Children's" },
  { value: "poetry", label: "Poetry" },
  { value: "other", label: "Other" },
];

const MARKETPLACES = [
  { value: "amazon_us", label: "Amazon US" },
  { value: "amazon_uk", label: "Amazon UK" },
  { value: "amazon_de", label: "Amazon DE" },
  { value: "amazon_ca", label: "Amazon CA" },
  { value: "amazon_au", label: "Amazon AU" },
];

const CURRENCIES = [
  { value: "USD", label: "USD" },
  { value: "GBP", label: "GBP" },
  { value: "EUR", label: "EUR" },
  { value: "CAD", label: "CAD" },
  { value: "AUD", label: "AUD" },
];

export function OrganizationTab() {
  const { data: orgSettings, isLoading } = useOrgSettings();
  const updateOrgSettings = useUpdateOrgSettings();

  // Form state
  const [formData, setFormData] = useState({
    name: "",
    website: "",
    industry: "",
    imprint_name: "",
    default_genre: "",
    default_marketplace: "",
    default_currency: "USD",
  });

  // Pre-fill form when data loads
  useEffect(() => {
    if (orgSettings) {
      setFormData({
        name: orgSettings.name || "",
        website: orgSettings.website || "",
        industry: orgSettings.industry || "",
        imprint_name: orgSettings.imprint_name || "",
        default_genre: orgSettings.default_genre || "",
        default_marketplace: orgSettings.default_marketplace || "",
        default_currency: orgSettings.default_currency || "USD",
      });
    }
  }, [orgSettings]);

  const handleInputChange = (field: string, value: string) => {
    setFormData((prev) => ({ ...prev, [field]: value }));
  };

  const handleSave = async () => {
    try {
      await updateOrgSettings.mutateAsync({
        name: formData.name,
        website: formData.website || undefined,
        industry: formData.industry || undefined,
        imprint_name: formData.imprint_name || undefined,
        default_genre: formData.default_genre || undefined,
        default_marketplace: formData.default_marketplace || undefined,
        default_currency: formData.default_currency || undefined,
      });
      toast.success("Organization settings updated successfully");
    } catch (error: any) {
      toast.error(error.message || "Failed to update organization settings");
    }
  };

  if (isLoading) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-64" />
        <Skeleton className="h-48" />
        <Skeleton className="h-64" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Organization Information */}
      <Card>
        <CardHeader>
          <CardTitle>Organization Information</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="org-name">Organization Name</Label>
              <Input
                id="org-name"
                type="text"
                value={formData.name}
                onChange={(e) => handleInputChange("name", e.target.value)}
                placeholder="Your Organization"
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="org-website">Website</Label>
              <Input
                id="org-website"
                type="url"
                value={formData.website}
                onChange={(e) => handleInputChange("website", e.target.value)}
                placeholder="https://example.com"
              />
            </div>
          </div>

          <div className="space-y-2">
            <Label htmlFor="org-industry">Industry</Label>
            <Select
              value={formData.industry}
              onValueChange={(value) => handleInputChange("industry", value)}
            >
              <SelectTrigger id="org-industry">
                <SelectValue placeholder="Select industry" />
              </SelectTrigger>
              <SelectContent>
                {INDUSTRIES.map((industry) => (
                  <SelectItem key={industry.value} value={industry.value}>
                    {industry.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </CardContent>
      </Card>

      {/* Publishing Imprint */}
      <Card>
        <CardHeader>
          <CardTitle>Publishing Imprint</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="imprint-name">Imprint Name</Label>
              <Input
                id="imprint-name"
                type="text"
                value={formData.imprint_name}
                onChange={(e) => handleInputChange("imprint_name", e.target.value)}
                placeholder="Your Publishing Imprint"
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="publisher-id">Publisher ID</Label>
              <div className="flex items-center gap-2">
                <Input
                  id="publisher-id"
                  type="text"
                  value={orgSettings?.publisher_id || "SPF-ORG-XXXXX"}
                  readOnly
                  disabled
                  className="bg-gray-50"
                />
                <Badge variant="secondary">Read-only</Badge>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Default Settings */}
      <Card>
        <CardHeader>
          <CardTitle>Default Settings</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="space-y-2">
              <Label htmlFor="default-genre">Default Genre</Label>
              <Select
                value={formData.default_genre}
                onValueChange={(value) => handleInputChange("default_genre", value)}
              >
                <SelectTrigger id="default-genre">
                  <SelectValue placeholder="Select genre" />
                </SelectTrigger>
                <SelectContent>
                  {GENRES.map((genre) => (
                    <SelectItem key={genre.value} value={genre.value}>
                      {genre.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label htmlFor="default-marketplace">Default Marketplace</Label>
              <Select
                value={formData.default_marketplace}
                onValueChange={(value) => handleInputChange("default_marketplace", value)}
              >
                <SelectTrigger id="default-marketplace">
                  <SelectValue placeholder="Select marketplace" />
                </SelectTrigger>
                <SelectContent>
                  {MARKETPLACES.map((marketplace) => (
                    <SelectItem key={marketplace.value} value={marketplace.value}>
                      {marketplace.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label htmlFor="default-currency">Default Currency</Label>
              <Select
                value={formData.default_currency}
                onValueChange={(value) => handleInputChange("default_currency", value)}
              >
                <SelectTrigger id="default-currency">
                  <SelectValue placeholder="Select currency" />
                </SelectTrigger>
                <SelectContent>
                  {CURRENCIES.map((currency) => (
                    <SelectItem key={currency.value} value={currency.value}>
                      {currency.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Team Members */}
      <Card>
        <CardHeader>
          <CardTitle>Team Members</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          {orgSettings?.team_members && orgSettings.team_members.length > 0 ? (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Name</TableHead>
                  <TableHead>Email</TableHead>
                  <TableHead>Role</TableHead>
                  <TableHead className="text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {orgSettings.team_members.map((member) => (
                  <TableRow key={member.id}>
                    <TableCell className="font-medium">{member.name}</TableCell>
                    <TableCell>{member.email}</TableCell>
                    <TableCell>
                      <Badge variant="secondary">{member.role}</Badge>
                    </TableCell>
                    <TableCell className="text-right">
                      <Button variant="ghost" size="sm">
                        Manage
                      </Button>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          ) : (
            <div className="text-center py-8 text-sm text-gray-500">
              No team members yet
            </div>
          )}

          <div className="flex justify-start gap-2">
            <Link href="/settings/team">
              <Button variant="outline" size="sm">
                Manage team &amp; roles →
              </Button>
            </Link>
          </div>
        </CardContent>
      </Card>

      {/* Save Button */}
      <div className="flex justify-end">
        <Button
          onClick={handleSave}
          disabled={updateOrgSettings.isPending}
        >
          {updateOrgSettings.isPending ? "Saving..." : "Save Changes"}
        </Button>
      </div>
    </div>
  );
}
