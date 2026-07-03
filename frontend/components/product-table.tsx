"use client";

import Link from "next/link";
import { useReactTable, getCoreRowModel, flexRender, createColumnHelper } from "@tanstack/react-table";

import type { ProductListItem } from "../lib/types";

const column = createColumnHelper<ProductListItem>();

const columns = [
  column.display({
    id: "select",
    header: ({ table }) => (
      <input
        aria-label="Select visible rows"
        type="checkbox"
        checked={table.getIsAllRowsSelected()}
        onChange={table.getToggleAllRowsSelectedHandler()}
      />
    ),
    cell: ({ row }) => <input type="checkbox" checked={row.getIsSelected()} onChange={row.getToggleSelectedHandler()} />,
  }),
  column.accessor("sku", { header: "SKU" }),
  column.accessor("title", { header: "Title", cell: (info) => info.getValue() ?? "" }),
  column.accessor("product_type", { header: "Product Type", cell: (info) => info.getValue() ?? "" }),
  column.accessor("attribute_set", { header: "Attribute Set", cell: (info) => info.getValue() ?? "" }),
  column.accessor("l1", { header: "Cat L1", cell: (info) => info.getValue() ?? "" }),
  column.accessor("l2", { header: "Cat L2", cell: (info) => info.getValue() ?? "" }),
  column.accessor("l3", { header: "Cat L3", cell: (info) => info.getValue() ?? "" }),
  column.accessor("l4", { header: "Cat L4", cell: (info) => info.getValue() ?? "" }),
  column.accessor("search_query", { header: "Search Query", cell: (info) => info.getValue() ?? "" }),
  column.accessor("updated_at", { header: "Last Updated", cell: (info) => new Date(info.getValue()).toLocaleString() }),
  column.display({
    id: "actions",
    header: "Actions",
    cell: ({ row }) => <Link href={`/products/${row.original.id}`}>View</Link>,
  }),
];

export function ProductTable({
  items,
  selected,
  onSelectedChange,
}: {
  items: ProductListItem[];
  selected: Record<string, boolean>;
  onSelectedChange: (selected: Record<string, boolean>) => void;
}) {
  const table = useReactTable({
    data: items,
    columns,
    getCoreRowModel: getCoreRowModel(),
    getRowId: (row) => row.id,
    state: { rowSelection: selected },
    onRowSelectionChange: (updater) => {
      onSelectedChange(typeof updater === "function" ? updater(selected) : updater);
    },
    enableRowSelection: true,
  });

  if (!items.length) {
    return <div className="panel muted">No products match the current filters.</div>;
  }

  return (
    <div className="table-wrap">
      <table>
        <thead>
          {table.getHeaderGroups().map((group) => (
            <tr key={group.id}>
              {group.headers.map((header) => (
                <th key={header.id}>{header.isPlaceholder ? null : flexRender(header.column.columnDef.header, header.getContext())}</th>
              ))}
            </tr>
          ))}
        </thead>
        <tbody>
          {table.getRowModel().rows.map((row) => (
            <tr key={row.id}>
              {row.getVisibleCells().map((cell) => (
                <td key={cell.id}>{flexRender(cell.column.columnDef.cell, cell.getContext())}</td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
