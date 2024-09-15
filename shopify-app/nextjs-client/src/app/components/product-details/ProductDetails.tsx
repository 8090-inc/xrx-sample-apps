import React, { useState, useEffect } from "react";
import { WidgetWrapper, ScrollableList, ItemCard } from "../base/Base";
import { motion } from "framer-motion";
import { ChatMessage } from "../../types/chat";
import baseStyles from "../base/Base.module.css";

interface Product {
  product_id: number;
  product_title: string;
  options: string[];
  product_variants: Array<{
    variant_id: number;
    variant_name: string;
    price: string;
    product_image_src?: string;
    product_variant_sku: string;
  }>;
  product_description?: string;
  inventory_quantity: number;
}

interface ProductDetailsProps {
  product: Product;
  loadingButtons: {
    [key: string]: boolean;
  };
  add_to_cart: (variant_id: number, quantity: number) => void;
  chatHistory: ChatMessage[];
}

const ProductDetails: React.FC<ProductDetailsProps> = ({
  product,
  loadingButtons,
  add_to_cart,
  chatHistory
}) => {
  const [emphasizedVariants, setEmphasizedVariants] = useState<number[]>([]);
  useEffect(() => {
    if (chatHistory.length > 0) {
      const lastMessage = chatHistory[chatHistory.length - 1];
      if (lastMessage.sender === "agent" && lastMessage.type !== "widget") {
        console.log(`lastMessage: ${JSON.stringify(lastMessage)}`);
        const sizeWords = ["small", "medium", "large", "extra"];
        const mentionedSizes = lastMessage.message
          .toLowerCase()
          // remove punctuation
          .replace(/[^a-zA-Z\s]/g, "")
          .split(" ")
          .filter((word) => {
            return sizeWords.includes(word);
          });
        // Remove 'large' if 'xtra' is mentioned
        if (mentionedSizes.includes("extra")) {
          const largeIndex = mentionedSizes.indexOf("large");
          if (largeIndex !== -1) {
            mentionedSizes.splice(largeIndex, 1);
          }
        }
        if (mentionedSizes.length > 0 && mentionedSizes.length <= 2) {
          const matchedVariants = product.product_variants.filter((variant) =>
            mentionedSizes.some((size) => {
              if (size === "extra") {
                return variant.variant_name.toLowerCase() === "extra large";
              } else {
                return variant.variant_name.toLowerCase() === size;
              }
            })
          );
          setEmphasizedVariants(matchedVariants.map((v) => v.variant_id));
        } else {
          setEmphasizedVariants([]);
        }
      }
    }
  }, [chatHistory, product.product_variants]);

  const makeSubtitle = (price: string) => {
    return `$${price}`;
  };

  return (
    <WidgetWrapper title={product.product_title}>
      {product.product_variants.map((variant) => (
        <ItemCard
          key={variant.variant_id}
          image={variant.product_image_src || "/placeholder-image.jpg"}
          title={
            variant.variant_name.toLowerCase() !== "default title"
              ? variant.variant_name
              : product.product_title
          }
          subtitle={makeSubtitle(variant.price)}
          actionIcon={
            loadingButtons[`add-${variant.variant_id}`] ? (
              <div className={baseStyles.loadingSpinner} />
            ) : (
              <motion.span>
                <svg
                  width="24"
                  height="24"
                  viewBox="0 0 24 24"
                  fill="none"
                  xmlns="http://www.w3.org/2000/svg"
                >
                  <path
                    d="M12 5V19M5 12H19"
                    stroke="currentColor"
                    strokeWidth="2"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  />
                </svg>
              </motion.span>
            )
          }
          onClick={() => {
            add_to_cart(variant.variant_id, 1);
          }}
          isHighlighted={emphasizedVariants.includes(variant.variant_id)}
        />
      ))}
    </WidgetWrapper>
  );
};

export default ProductDetails;
