"use client";

import { TeamMembersList } from "@/modules/team/components/TeamMembersList";
import { RolesList } from "@/modules/team/components/RolesList";
import { Separator } from "@/components/ui/separator";

export default function TeamSettingsPage() {
  return (
    <div className="space-y-8">
      <div>
        <h2 className="text-lg font-semibold">Team &amp; Permissions</h2>
        <p className="text-sm text-muted-foreground">
          Invite teammates, assign roles, and configure custom permission
          profiles for editors, designers, and virtual assistants.
        </p>
      </div>
      <Separator />
      <TeamMembersList />
      <Separator />
      <RolesList />
    </div>
  );
}
