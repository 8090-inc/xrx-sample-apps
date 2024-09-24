import React from "react";
import { WidgetWrapper, ScrollableList, ItemCard } from "../base/Base";
import baseStyles from "../base/Base.module.css";

interface Product {
  product_id: number;
  product_title: string;
  product_image_src: string;
  inventory_quantity: number;
}

interface MenuProps {
  products: { [key: string]: Product };
  loadingButtons?: { [key: string]: boolean };
  showDetails?: (element: any, productId: number) => void;
}

const Menu: React.FC<MenuProps> = ({
  products,
  loadingButtons,
  showDetails = () => {}
}) => {
  return (
    <WidgetWrapper title="MENU">
      {Object.entries(products).map(
        ([productId, product]: [string, Product]) => (
          <ItemCard
            key={product.product_id}
            image={product.product_image_src}
            title={product.product_title}
            onClick={(event: any) =>
              showDetails(event.target, product.product_id)
            }
            actionIcon={
              loadingButtons &&
              loadingButtons[`details-${product.product_id}`] ? (
                <div className={baseStyles.loadingSpinner} />
              ) : (
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" style={{ marginLeft: '1px' }}>
                  <path d="M9 18L15 12L9 6" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                </svg>
              )
            }
          />
        )
      )}
    </WidgetWrapper>
  );
};

export default Menu;
