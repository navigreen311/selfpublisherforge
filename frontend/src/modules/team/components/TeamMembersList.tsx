"use client";

import { useState } from "react";
import { Plus, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  useAssignRole,
  useInvitations,
  useRemoveMember,
  useResendInvite,
  useRoles,
  useTeam,
} from "../hooks";
import { InviteModal } from "./InviteModal";

export function TeamMembersList() {
  const { data: team = [], isLoading } = useTeam();
  const { data: invitations = [] } = useInvitations();
  const { data: roles = [] } = useRoles();
  const [inviteOpen, setInviteOpen] = useState(false);
  const assign = useAssignRole();
  const remove = useRemoveMember();
  const resend = useResendInvite();

  if (isLoading) {
    return (
      <div className="flex items-center gap-2 text-muted-foreground">
        <Loader2 className="h-4 w-4 animate-spin" /> Loading team…
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-base font-medium">Team Members</h3>
          <p className="text-sm text-muted-foreground">
            Invite teammates and assign them roles.
          </p>
        </div>
        <Button size="sm" onClick={() => setInviteOpen(true)}>
          <Plus className="h-4 w-4 mr-1" /> Invite Team Member
        </Button>
      </div>

      <div className="rounded-lg border overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-muted">
            <tr>
              <th className="text-left p-3 font-medium">Member</th>
              <th className="text-left p-3 font-medium">Email</th>
              <th className="text-left p-3 font-medium">Role</th>
              <th className="text-left p-3 font-medium">Status</th>
              <th className="text-left p-3 font-medium">Actions</th>
            </tr>
          </thead>
          <tbody>
            {team.map((m) => (
              <tr
                key={m.user_id}
                className="border-t"
                data-testid="team-member-row"
              >
                <td className="p-3">{m.name ?? "—"}</td>
                <td className="p-3">{m.email}</td>
                <td className="p-3">
                  {m.role_name === "Owner" ? (
                    <Badge variant="secondary">Owner</Badge>
                  ) : (
                    <Select
                      value={m.role_id ?? ""}
                      onValueChange={(v) =>
                        assign.mutate({ userId: m.user_id, roleId: v })
                      }
                    >
                      <SelectTrigger className="w-32">
                        <SelectValue placeholder="No role" />
                      </SelectTrigger>
                      <SelectContent>
                        {roles.map((r) => (
                          <SelectItem key={r.id} value={r.id}>
                            {r.name}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  )}
                </td>
                <td className="p-3">
                  <Badge variant="outline">{m.status}</Badge>
                </td>
                <td className="p-3">
                  {m.role_name !== "Owner" && (
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => {
                        if (confirm(`Remove ${m.email}?`))
                          remove.mutate(m.user_id);
                      }}
                    >
                      Remove
                    </Button>
                  )}
                </td>
              </tr>
            ))}
            {invitations
              .filter((i) => i.status === "pending")
              .map((inv) => (
                <tr key={inv.id} className="border-t bg-muted/30">
                  <td className="p-3 text-muted-foreground italic">Pending</td>
                  <td className="p-3">{inv.email}</td>
                  <td className="p-3">{inv.role_name ?? "—"}</td>
                  <td className="p-3">
                    <Badge variant="outline">Invited</Badge>
                  </td>
                  <td className="p-3">
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => resend.mutate(inv.id)}
                    >
                      Resend
                    </Button>
                  </td>
                </tr>
              ))}
          </tbody>
        </table>
      </div>

      <InviteModal open={inviteOpen} onOpenChange={setInviteOpen} />
    </div>
  );
}
