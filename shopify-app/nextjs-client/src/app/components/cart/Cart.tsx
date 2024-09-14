import React from "react";
import { motion } from "framer-motion";
import Image from "next/image";
import { WidgetWrapper, ScrollableList, ItemCard } from "../base/Base";
import baseStyles from "../base/Base.module.css";
import styles from "./Cart.module.css";

interface CartItem {
  name: string;
  quantity: number;
  price: string;
  variant_id: number;
  product_id?: number;
  item_variant_sku?: string;
  variant_title?: string;
  product_image_src: string;
  deleteAction: (element: any, variant_id: number) => void;
}

interface CartProps {
  cart: any;
  loadingButtons: { [key: string]: boolean };
  deleteAction: (element: any, variant_id: number) => void;
}

const Cart: React.FC<CartProps> = ({ cart, loadingButtons, deleteAction }) => {
  const formatTitle = (item: CartItem) => {
    switch (item.name) {
      case "Brooklyn Style Pizza":
        return `${item.name} (${item.variant_title})`;
      case "Chicken Wings":
        return `${item.name} (${item.variant_title})`;
      case "Drinks":
        return `${item.variant_title}`;
      default:
        return item.name;
    }
  };
  return (
    <WidgetWrapper title="CART">
      {cart.cart_summary.line_items.length === 0 ? (
        <div className={styles.emptyCart}>
          <p>Your cart is empty</p>
          <p>Add some items to get started!</p>
        </div>
      ) : (
        cart.cart_summary.line_items.map((item: CartItem) => (
          <ItemCard
            key={item.variant_id}
            image={item.product_image_src}
            title={formatTitle(item)}
            subtitle={`${item.quantity} x $${item.price}`}
            onClick={(event: any) =>
              deleteAction(event.target, item.variant_id)
            }
            actionIcon={
              loadingButtons[`delete-${item.variant_id}`] ? (
                <div className={baseStyles.loadingSpinner} />
              ) : (
                <Image src="/trash.svg" alt="Delete" width={20} height={20} />
              )
            }
          />
        ))
      )}

      <motion.div
        className={styles.cartTotal}
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.3 }}
      >
        <div className={styles.cartTotalText}>TOTAL</div>
        <div className={styles.cartTotalPrice}>
          <span
            style={{
              color: "var(--font-color-on-background)",
              fontSize: "1.1rem"
            }}
          >
            $
          </span>{" "}
          {cart.cart_summary.total_price}
        </div>
      </motion.div>
    </WidgetWrapper>
  );
};

export default Cart;
