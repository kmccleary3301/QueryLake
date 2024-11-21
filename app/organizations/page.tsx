"use client";

import { ScrollArea, ScrollAreaHorizontal } from "@/components/ui/scroll-area";
import { Table, TableBody, TableCaption, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { useContextAction } from "@/app/context-provider";
import { useEffect, useState } from "react";
import { user_organization_membership, QueryLakeCreateOrganization, QueryLakeFetchUsersMemberships, organization_memberships, QueryLakeFetchOrganizationsMemberships, QueryLakeInviteUserToOrg, memberRoleLower } from "@/hooks/querylakeAPI";
import { Button } from "@/components/ui/button";
import { motion } from "framer-motion";

interface OrgPageProps {
  params: {
    slug: string[],
  },
  searchParams: object
}

import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import {
  Sheet,
  SheetClose,
  SheetContent,
  SheetDescription,
  SheetFooter,
  SheetHeader,
  SheetTitle,
  SheetTrigger,
} from "@/components/ui/sheet"
import { toast } from 'sonner';
import { ComboBox, ComboBoxScrollPreview } from "@/components/ui/combo-box";

export function CreateOrgSheet({
  children,
  onSubmit,
}:{
  children: React.ReactNode,
  onSubmit: (form : {
    name: string
  }) => void
}) {
  const [name, setName] = useState("");


  return (
    <Sheet>
      <SheetTrigger asChild>
        {children}
      </SheetTrigger>
      <SheetContent>
        <SheetHeader>
          <SheetTitle>Create Organization</SheetTitle>
          <SheetDescription>
            Create a new QueryLake organization. 
          </SheetDescription>
        </SheetHeader>
        <div className="grid gap-4 py-4">
          <div className="grid grid-cols-4 items-center gap-4">
            <Label htmlFor="name" className="text-right">
              Name
            </Label>
            <Input id="name" value={name} onChange={
              (e) => setName(e.target.value)
            } placeholder="Set Organization Name" className="col-span-3" />
          </div>
        </div>
        <SheetFooter >
          <SheetClose asChild>
            <Button type="submit" variant={"secondary"} disabled={(name==="")} onClick={() => {onSubmit({name: name})}}>Create</Button>
          </SheetClose>
        </SheetFooter>
      </SheetContent>
    </Sheet>
  )
}

type memberRole = "Owner" | "Admin" | "Member" | "Reader";

export function InviteUserToOrgSheet({
  children,
  onSubmit,
}:{
  children: React.ReactNode,
  onSubmit: (form : {
    name: string,
    role: memberRole
  }) => void
}) {
  const [name, setName] = useState("");
  const [role, setRole] = useState<memberRole>("Reader");


  return (
    <Sheet>
      <SheetTrigger asChild>
        {children}
      </SheetTrigger>
      <SheetContent>
        <SheetHeader>
          <SheetTitle>Invite User</SheetTitle>
          <SheetDescription>
            Invite a user to join this organization.
          </SheetDescription>
        </SheetHeader>
        <div className="grid gap-4 py-4">
          <div className="grid grid-cols-4 items-center gap-4">
            <Label htmlFor="name" className="text-right">
              User
            </Label>
            <Input id="name" value={name} onChange={
              (e) => setName(e.target.value)
            } placeholder="Username to invite" className="col-span-3" />
          </div>
          <div className="grid grid-cols-4 items-center gap-4">
            <Label htmlFor="role" className="text-right">
              Role
            </Label>
            <ComboBoxScrollPreview
              values={[
                {
                  value: "Owner",
                  label: "Owner",
                  preview: "Can delete organization and manage all members."
                },
                {
                  value: "Admin",
                  label: "Admin",
                  preview: "Can manage all members and document collections."
                },
                {
                  value: "Member",
                  label: "Member",
                  preview: "Can view and edit document collections."
                },
                {
                  value: "Reader",
                  label: "Reader",
                  preview: "Can view organization data and read documents."
                },
              ]}
              onChange={(value) => {
                setRole(value as memberRole);
              }}
              value={role}
            />
          </div>
        </div>
        <SheetFooter >
          <SheetClose asChild>
            <Button type="submit" variant={"secondary"} disabled={(name==="")} onClick={() => {onSubmit({name: name, role: role})}}>
              Send Invite
            </Button>
          </SheetClose>
        </SheetFooter>
      </SheetContent>
    </Sheet>
  )
}


export default function OrgPage({ params, searchParams }: OrgPageProps) {
  const { slug } = params;
  const { userData } = useContextAction();
  const [organizations, setOrganizations] = useState<user_organization_membership[]>([]);
  const [selectedOrg, setSelectedOrg] = useState<user_organization_membership | undefined>();
  const [selectedOrgMembers, setSelectedOrgMembers] = useState<organization_memberships[]>([]);

  useEffect(() => {
    QueryLakeFetchUsersMemberships({
      auth: userData?.auth as string,
      onFinish: (data) => {
        if (data === false) { return; }
        setOrganizations(data);
      }
    })
  }, [userData])

  useEffect(() => {
    if (selectedOrg === undefined) { return; }
    QueryLakeFetchOrganizationsMemberships({
      auth: userData?.auth as string,
      organization_id: selectedOrg.organization_id,
      onFinish: (data) => {
        if (data === false) { return; }
        setSelectedOrgMembers(data);
      }
    })
  }, [userData, selectedOrg])


  
  return (
    <div className="w-[100%] h-screen absolute">
    <ScrollAreaHorizontal className="h-screen w-full flex flex-row">
      <p className="text-5xl text-primary/80 text-bold py-[20px] w-full border-0 border-outline border-b-2 h-[100px] text-center">
        <strong>{"Manage Organizations"}</strong>
      </p>
      <div className="h-[calc(100vh-140px)] flex flex-row">
        <ScrollArea className="w-[26rem] pr-2 border-2 border-outline border-t-0 h-[calc(100vh-100px)]">
          <Table className="w-[25rem]">

          <TableCaption>All Memberships</TableCaption>

          <TableHeader>
            <TableRow>
              <TableHead>Org Name</TableHead>
              <TableHead>Role</TableHead>
              <TableHead>Resolved</TableHead>
              <TableHead></TableHead>
            </TableRow>
          </TableHeader>

          <TableBody>
            <TableRow>

              <TableCell colSpan={4} className="text-center p-0">
                <CreateOrgSheet onSubmit={(form) => {
                  toast("Creating organization");
                  QueryLakeCreateOrganization({
                    auth: userData?.auth as string,
                    organization_name: form.name,
                    onFinish: (data) => {
                      if (data === false) {
                        toast("Failed to create organization");
                        return; 
                      }
                      toast("Organization created successfully");
                      setOrganizations([...organizations, {
                        organization_id: data.organization_id,
                        organization_name: form.name,
                        role: "Owner",
                        invite_still_open: false,
                        sender: userData?.username as string,
                      }]);
                    }
                  })


                }}>
                  <Button variant={"ghost"} className="w-full rounded-none">
                    Create New Organization
                  </Button>
                </CreateOrgSheet>
              </TableCell>
            </TableRow>
            
            {organizations.map((org, org_index) => (
              <TableRow key={org_index}>
                <TableCell className="font-medium">{org.organization_name}</TableCell>
                <TableCell>{org.role}</TableCell>
                <TableCell>
                  {(org.invite_still_open)?(
                    <p>{"Accept"}</p>
                  ):(
                    <p>{"Accepted"}</p>
                  )}
                </TableCell>
                <TableCell>
                  <Button variant={"secondary"} className="w-[4rem]" onClick={() => {
                    if (selectedOrg === org) {
                      setSelectedOrg(undefined);
                      setSelectedOrgMembers([]);
                    } else {
                      setSelectedOrg(org);
                    }
                  }}>
                    {(selectedOrg === org) ? "Close" : "View"}
                  </Button>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>

          </Table>
        </ScrollArea>

        
        <div className="h-[calc(100vh-100px)] ">
          <motion.div
            className="h-[calc(100vh-100px)] overflow-hidden"
            animate={{
              width: (selectedOrg !== undefined) ? "26rem" : "0rem"
            }}
            initial={{
              width: "0rem"
            }}
            transition={{ duration: 0.3 }}
          >
            <ScrollArea className="w-[26rem] pr-2 h-[calc(100vh-100px)] border-2 border-outline border-t-0 border-l-0">
              <Table className="w-[25rem]">

              <TableCaption>Org Members</TableCaption>

              <TableHeader>
                <TableRow>
                  <TableHead>User</TableHead>
                  <TableHead>Role</TableHead>
                  <TableHead>Resolved</TableHead>
                </TableRow>
              </TableHeader>

              <TableBody>
                

                {((selectedOrg?.role === "admin") || 
                  (selectedOrg?.role === "owner") || 
                  (selectedOrg?.role === "member")) && (

                  <TableRow>
                    <TableCell colSpan={4} className="text-center p-0">
                      <InviteUserToOrgSheet onSubmit={(form) => {
                        toast("Inviting User");
                        QueryLakeInviteUserToOrg({
                          auth: userData?.auth as string,
                          organization_id: selectedOrg?.organization_id as string,
                          username: form.name,
                          role: (form.role).toLowerCase() as memberRoleLower,
                          onFinish: (data) => {
                            if (data === false) {
                              toast("Failed to invite user");
                              return; 
                            }
                            toast("User invited successfully");
                            setSelectedOrgMembers([...selectedOrgMembers, {
                              username: form.name,
                              role: (form.role as string).toLowerCase() as memberRole,
                              invite_still_open: true,
                              organization_id: selectedOrg?.organization_id as string,
                              organization_name: selectedOrg?.organization_name as string,
                            }]);
                          }
                        })
                      }}>
                        <Button variant={"ghost"} className="w-full rounded-none">
                          Invite New User
                        </Button>
                      </InviteUserToOrgSheet>
                    </TableCell>
                  </TableRow>
                )}

                {selectedOrgMembers.map((member, member_index) => (
                  <TableRow key={member_index}>
                    <TableCell className="font-medium">{member.username}</TableCell>
                    <TableCell>{member.role}</TableCell>
                    <TableCell>
                      {(member.invite_still_open)?(
                        <p>{"Pending"}</p>
                      ):(
                        <p>{"Accepted"}</p>
                      )}
                    </TableCell>
                    
                  </TableRow>
                ))}
              </TableBody>

              </Table>
            </ScrollArea>

          </motion.div>
        </div>

      </div>
    </ScrollAreaHorizontal>
    </div>
  );
}