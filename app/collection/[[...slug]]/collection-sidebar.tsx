import * as React from "react"

import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarGroup,
  SidebarGroupContent,
  SidebarGroupLabel,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  SidebarMenuSub,
  SidebarMenuSubButton,
  SidebarMenuSubItem,
  SidebarRail,
} from "@/components/ui/sidebar"
import { ComboBox, ComboBoxScrollPreview } from "@/components/ui/combo-box"
import { userDataType } from "@/types/globalTypes"
import { Button } from "@/components/ui/button"
import { modifyCollection, QueryLakeChangeCollectionOwnership } from "@/hooks/querylakeAPI"
import { toast } from "sonner"
import CompactInput from "@/components/ui/compact-input"
import { Textarea } from "@/components/ui/textarea"
import { useContextAction } from "@/app/context-provider"
import { Label } from "@/components/ui/label"
import { Input } from "@/components/ui/input"

export function CollectionSidebar({
	collection_id,
	user_auth,
	collection_is_public,
	set_collection_is_public,
	collection_owner,
	set_collection_owner,
	collection_name,
	set_collection_name,
	collection_description,
	set_collection_description,
	...props 
}:React.ComponentProps<typeof Sidebar> & {
	user_auth: userDataType,
	collection_id: string,
	collection_is_public: boolean,
	set_collection_is_public: React.Dispatch<React.SetStateAction<boolean>>,
	collection_owner: string,
	set_collection_owner: React.Dispatch<React.SetStateAction<string>>,
	collection_name: string,
	set_collection_name: React.Dispatch<React.SetStateAction<string>>,
	collection_description: string,
	set_collection_description: React.Dispatch<React.SetStateAction<string>>,
}) {
	const { refreshCollectionGroups } = useContextAction();


	const [tempOwner, setTempOwner] = React.useState(collection_owner);
	const [tempPublic, setTempPublic] = React.useState(collection_is_public);
	const [tempName, setTempName] = React.useState(collection_name);
	const [tempDescription, setTempDescription] = React.useState(collection_description);

	React.useEffect(() => {
		setTempOwner(collection_owner);
		setTempPublic(collection_is_public);
		setTempName(collection_name);
		setTempDescription(collection_description);
	}, [collection_owner, collection_is_public, collection_name, collection_description]);

	const saveChangesOwnership = React.useCallback(() => {
		QueryLakeChangeCollectionOwnership({
			auth: user_auth?.auth as string,
			username: user_auth.username,
			owner: tempOwner,
			public: tempPublic,
			collection_id: collection_id,
			onFinish: (result : boolean) => {
				if (result) {
					set_collection_owner(tempOwner);
					set_collection_is_public(tempPublic);
					toast("Changed owner/public successfully.");
				} else {
					toast("Failed to save changes.");
				}
			}
		})
	}, [tempPublic, collection_is_public, tempOwner, collection_owner, collection_id]);

	const saveChangesMetadata = React.useCallback(() => {
		modifyCollection({
			auth: user_auth?.auth as string,
			public: collection_is_public,
			collection_id: collection_id,
			description: tempDescription,
			title: tempName,
			onFinish: (result) => {

			}
		})
	}, [collection_name, tempName, collection_description, tempDescription, collection_id]);

	const all_available_orgs = [
		{category_label: "Self", values: [
			{value: "personal", label: "Personal", preview: "Collection belongs to you."},
			{value: "global", label: "Global", preview: "Collection is viewable by everyone."},
		]},
		{category_label: "Organizations", values: user_auth.memberships.filter((membership) => {
			return (membership.role === "owner") || (membership.role === "admin");
		}).map((membership) => {
			return {
				value: membership.organization_id, 
				label: membership.organization_name, 
				preview: "Collection belongs to " + membership.organization_name + "."
			}
		})}
	];

	React.useEffect(() => {
		console.log("Temp Owner:", tempOwner);
		console.log("All orgs:", all_available_orgs);
	}, []);

  return (
    <Sidebar {...props}>
      <SidebarContent>
        <SidebarGroup>
          <SidebarGroupLabel>Modify Collection</SidebarGroupLabel>
          <SidebarGroupContent className="space-y-4 flex flex-col">
						<div className="flex flex-col space-y-2">
							<Label>Owner</Label>
							<ComboBoxScrollPreview
								value={tempOwner} 
								onChange={(value: string) => {
									setTempOwner(value);
								}}
								values={all_available_orgs}
							/>
						</div>
						<div className="flex flex-col space-y-2">
							<Label>Visibility</Label>
							<ComboBox
								value={(tempPublic) ? "public" : "private"} 
								onChange={(value_change: string) => {
									if (value_change === "public") {
										setTempPublic(true);
									} else {
										setTempPublic(false);
									}
								}}
								values={[
									{value: "private", label: "Private", preview: "Collection is private, only people with access can view it."},
									{value: "public", label: "Public", preview: "Collection is viewable by everyone."},
								]}
							/>
						</div>
						<div className="flex flex-col space-y-2">
							<Label>Title</Label>
							<Input
								value={tempName}
								placeholder="Collection Name"
								onChange={(e) => {
									setTempName(e.target.value);
								}}
							/>
						</div>
						<div className="flex flex-col space-y-2">
							<Label>Description</Label>
							<Textarea
								value={tempDescription}
								placeholder="Collection Description"
								className="resize-none"
								rows={10}
								onChange={(e) => {
									setTempDescription(e.target.value);
								}}
							/>
						</div>

          </SidebarGroupContent>
        </SidebarGroup>
      </SidebarContent>
			<SidebarFooter>
				<Button 
					onClick={() => {
						if ((tempOwner !== collection_owner) || (tempPublic !== collection_is_public)) {
							saveChangesOwnership();
						}
						if ((tempName !== collection_name) || (tempDescription !== collection_description)) {
							saveChangesMetadata();
						}
						refreshCollectionGroups();
					}} 
					disabled={
						(tempOwner === collection_owner) &&
						(tempPublic === collection_is_public) &&
						(tempName === collection_name) &&
						(tempDescription === collection_description)
					}
				>
					Save
				</Button>
			</SidebarFooter>
      <SidebarRail />
    </Sidebar>
  )
}
