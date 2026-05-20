export type SKUItem = {
  sku_number: string;
  description: string;
  unit_of_measure: string;
  unit_price: number;
  msrp?: number | null;
  min_order_qty: number;
  lead_time: string;
  status: string;
};

export const EMPTY_SKU: SKUItem = {
  sku_number: "",
  description: "",
  unit_of_measure: "EA",
  unit_price: 0,
  msrp: null,
  min_order_qty: 1,
  lead_time: "14 days",
  status: "Active",
};

export const SKU_STATUSES = ["Active", "Inactive", "Pending", "Discontinued"] as const;
export const SKU_UOMS = ["EA", "CS", "BX", "PK", "PR", "KG", "LB"] as const;
