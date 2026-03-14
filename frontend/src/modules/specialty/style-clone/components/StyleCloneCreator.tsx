"use client";
import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
interface Props { onCreated: () => void; onCancel: () => void; }
export function StyleCloneCreator({ onCreated, onCancel }: Props) { const [name, setName] = useState(""); return (<div className="space-y-4"><div className="space-y-2"><Label htmlFor="sn">Name</Label><Input id="sn" value={name} onChange={(e) => setName(e.target.value)} placeholder="Name" /></div><div className="flex justify-end gap-2"><Button variant="outline" onClick={onCancel}>Cancel</Button><Button onClick={onCreated} disabled={!name}>Create</Button></div></div>); }
